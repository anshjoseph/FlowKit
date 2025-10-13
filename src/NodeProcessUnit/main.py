import os
import uuid
import time
import random
import dotenv
import requests
import tempfile
import threading
from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
import platform
from pathlib import Path
import subprocess
import aiohttp
from pydantic import BaseModel
from typing import List, Dict, Union, Literal
import httpx
from queue import Queue
from base64 import b64decode
import json
from threading import Thread, Event, Lock
import logging
import asyncio

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('npu_node.log')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
dotenv.load_dotenv(".env")
logger.info("Environment variables loaded")

# Configuration flags
LOCAL = True

# Environment variables with defaults
HOST = os.getenv("HOST", "0.0.0.0")
NODE_RUNNER_ADDR = os.getenv("NODE_RUNNER_ADDR", "http://127.0.0.1:8500")
VENV_PATH = os.getenv("VENV_PATH")
PARALLEL_PROCESS = int(os.getenv("PARALLEL_PROCESS", "4"))

# Generate random port and unique node ID
PORT = random.randint(10000, 11000)
NODE_ID = str(uuid.uuid4())
START_TIME = time.time()

logger.info(f"Node configuration - ID: {NODE_ID}, Port: {PORT}, Parallel processes: {PARALLEL_PROCESS}")

# Task queue for worker threads
QUEUE = Queue()

# ============================================================================
# PYTHON SANDBOX PATH RESOLUTION
# ============================================================================
python_sandbox_path = Path(VENV_PATH).resolve()
os_name = platform.system()

logger.info(f"Detected OS: {os_name}")

# Determine Python executable path based on OS
if os_name == "Linux" or os_name == "Darwin":
    python_sandbox_path = python_sandbox_path / "bin" / "python"
elif os_name == "Windows":
    python_sandbox_path = python_sandbox_path / "Scripts" / "python.exe"
else:
    python_sandbox_path = python_sandbox_path / "bin" / "python"

python_sandbox_path = python_sandbox_path.resolve()
logger.info(f"Python sandbox path: {python_sandbox_path}")

# Validate Python executable exists
if not python_sandbox_path.exists():
    logger.error(f"Python executable not found at: {python_sandbox_path}")
    raise FileNotFoundError(f"Python executable not found at: {python_sandbox_path}")

# ============================================================================
# STATUS TRACKING
# ============================================================================
status = {
    "successful_tasks": 0,
    "failed_tasks": 0,
    "queued_tasks": 0
}

# Thread-safe lock for status updates
status_lock = Lock()

# ============================================================================
# BACKGROUND METRICS POLLING
# ============================================================================
def start_metrics_poller():
    """
    Background thread that periodically sends NPU metrics to the node runner.
    Updates every 7 seconds with current uptime, task counts, and queue size.
    """
    logger.info("Metrics poller started")
    
    while True:
        try:
            with status_lock:
                payload = {
                    "uptime": time.time() - START_TIME,
                    "successful_tasks": status["successful_tasks"],
                    "failed_tasks": status["failed_tasks"],
                    "queued_tasks": QUEUE.qsize()
                }
            
            logger.debug(f"Sending metrics update: {payload}")
            
            response = requests.post(
                f"{NODE_RUNNER_ADDR}/npu/pool/{NODE_ID}",
                json=payload,
                timeout=5,
            )
            response.raise_for_status()
            logger.debug("Metrics update successful")
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Metrics update failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in metrics poller: {e}", exc_info=True)
        
        time.sleep(7)


# ============================================================================
# NPU LOG SENDER
# ============================================================================
async def send_npu_log(runner_id: str, log_message: str):
    """
    Send a log message to the NPU log API endpoint.
    
    Args:
        runner_id: UUID string of the node runner
        log_message: Log message to send
    """
    url = f"{NODE_RUNNER_ADDR}/npu/log/{runner_id}"
    params = {"log": log_message}
    
    logger.debug(f"Sending log for runner {runner_id}: {log_message}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, params=params) as response:
                if response.status == 201:
                    logger.info(f"Log sent successfully for runner {runner_id}")
                else:
                    text = await response.text()
                    logger.error(f"Failed to send log for runner {runner_id}: {response.status}, {text}")
    except Exception as e:
        logger.error(f"Exception while sending log for runner {runner_id}: {e}", exc_info=True)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================
class NodeResult(BaseModel):
    """Result of a node execution"""
    nodes: List[str]
    outputs: Dict[str, Union[str, int, float]]
    message: str
    status: Literal["DONE", "ERROR"]


class Node(BaseModel):
    """Node execution request"""
    inputs: Dict[str, Union[str, int, float]]
    code: str
    runner_id: str
    node_name: str


# ============================================================================
# NODE RESULT SENDER
# ============================================================================
async def send_node_result(node_id: str, result: NodeResult):
    """
    Send execution result back to the node runner.
    
    Args:
        node_id: ID of the node
        result: NodeResult object containing execution results
    """
    url = f"{NODE_RUNNER_ADDR}/npu/result/{node_id}"
    logger.info(f"Sending result for node {node_id}, status: {result.status}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url, 
                json=result.dict(), 
                headers={"accept": "application/json"},
                timeout=10.0
            )
            response.raise_for_status()
            logger.info(f"Result sent successfully for node {node_id}")
            return response.text
    except httpx.HTTPError as e:
        logger.error(f"HTTP error sending result for node {node_id}: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending result for node {node_id}: {e}", exc_info=True)
        raise


# ============================================================================
# QUEUE MANAGEMENT
# ============================================================================
queue_lock = Lock()

def get_data_from_queue() -> Node:
    """
    Thread-safe queue retrieval.
    
    Returns:
        Node object if available, None if queue is empty
    """
    with queue_lock:
        if QUEUE.empty():
            return None
        else:
            node = QUEUE.get_nowait()
            logger.debug(f"Retrieved node from queue: {node.node_name}")
            return node


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def b64_to_str(b64_text: str) -> str:
    """
    Decode base64 encoded string to UTF-8.
    
    Args:
        b64_text: Base64 encoded string
        
    Returns:
        Decoded UTF-8 string
    """
    try:
        return b64decode(b64_text).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode base64 string: {e}")
        raise


# ============================================================================
# OPTIMIZED PYTHON CODE EXECUTION
# ============================================================================
def execute_python_code_optimized(
    code: str, 
    runner_id: str, 
    inputs: Dict[str, Union[float, int, str]], 
    node_name: str
) -> tuple:
    """
    Execute Python code in a sandboxed environment with optimized file handling.
    Uses delete=False for better performance and explicit cleanup.
    """
    logger.info(f"Executing code for node: {node_name}, runner: {runner_id}")
    
    python_file_path = None
    json_file_path = None
    
    try:
        # Decode code once
        python_code = b64_to_str(code)
        
        # Create temporary Python file (delete=False for speed)
        python_fd, python_file_path = tempfile.mkstemp(suffix=".py", text=True)
        with os.fdopen(python_fd, 'w') as f:
            f.write(python_code)
        logger.debug(f"Created temp Python file: {python_file_path}")

        # Create temporary JSON input file (delete=False for speed)
        json_fd, json_file_path = tempfile.mkstemp(suffix=".json", text=True)
        with os.fdopen(json_fd, 'w') as f:
            json.dump(inputs, f)
        logger.debug(f"Created temp JSON file: {json_file_path}")

        self_addr = f"http://127.0.0.1:{PORT}"
        
        # Build command arguments
        cmd_args = [
            str(python_sandbox_path),
            python_file_path,
            json_file_path,
            runner_id,
            self_addr,
            node_name
        ]
        
        logger.debug(f"Executing subprocess for node: {node_name}")
        
        _s = time.time()
        # Execute subprocess with optimized settings
        result = subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=30,
            # Optimization: don't pass shell=True (slower)
            shell=False
        )
        exec_time = time.time() - _s
        logger.info(f"EXEC TIME for {node_name}: {exec_time:.3f}s")
        
        if result.stdout:
            logger.debug(f"STDOUT: {result.stdout[:200]}")  # Log first 200 chars only
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr[:200]}")

        return result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        error_msg = f"Code execution timeout for node: {node_name}"
        logger.error(error_msg)
        return "", error_msg

    except Exception as e:
        error_msg = f"Code execution error for node {node_name}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return "", error_msg

    finally:
        # Cleanup temporary files
        for path in [python_file_path, json_file_path]:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
                    logger.debug(f"Deleted temp file: {path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp file {path}: {e}")


# ============================================================================
# OPTIMIZED WORKER THREADS
# ============================================================================
class Worker(Thread):
    """
    Optimized worker thread that processes nodes from the queue.
    Removed unnecessary subprocess shell initialization.
    """
    
    def __init__(self, name: str):
        super().__init__(target=self.run, name=name, daemon=True)
        self.__stop_event = Event()
        logger.info(f"Worker initialized: {name}")

    def run(self):
        """Main worker loop - processes nodes from queue"""
        logger.info(f"Worker {self.name} started")
        
        while not self.__stop_event.is_set():
            try:
                node: Node = get_data_from_queue()
                
                if node is None:
                    # No work available, sleep briefly
                    time.sleep(0.05)  # Reduced from 0.1 for faster response
                    continue
                
                logger.info(f"Worker {self.name} processing node: {node.node_name}")
                
                # Execute the node's code with optimized function
                stdout, stderr = execute_python_code_optimized(
                    node.code, 
                    node.runner_id, 
                    node.inputs, 
                    node.node_name
                )
                
                # Log results if present
                if stdout:
                    logger.debug(f"Worker {self.name} - Node {node.node_name} completed with output")
                
                if stderr:
                    logger.warning(f"Worker {self.name} - Node {node.node_name} had stderr output")
                
                logger.info(f"Worker {self.name} completed node: {node.node_name}")
                
            except Exception as e:
                logger.error(f"Worker {self.name} encountered error: {e}", exc_info=True)
                time.sleep(0.1)  # Brief pause on error to prevent tight error loops
        
        logger.info(f"Worker {self.name} stopped")
    
    def stop(self):
        """Signal the worker to stop processing"""
        logger.info(f"Stopping worker: {self.name}")
        self.__stop_event.set()


# ============================================================================
# GLOBAL WORKER LIST
# ============================================================================
WORKERS: List[Worker] = []


# ============================================================================
# FASTAPI LIFESPAN MANAGEMENT
# ============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown lifecycle.
    - Registers NPU with node runner
    - Starts worker threads
    - Starts metrics polling
    """
    global START_TIME, WORKERS
    
    START_TIME = time.time()
    logger.info("Application startup initiated")
    
    # Determine public address
    if LOCAL:
        address = f"http://127.0.0.1:{PORT}"
    else:
        address = f"http://{HOST}:{PORT}"
    
    payload = {"address": address, "id": NODE_ID}

    # Register NPU with node runner
    try:
        logger.info(f"Registering NPU with node runner at {NODE_RUNNER_ADDR}")
        res = requests.post(
            f"{NODE_RUNNER_ADDR}/npu/add", 
            json=payload, 
            timeout=5
        )
        res.raise_for_status()
        logger.info(f"Successfully registered NPU -> {payload}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to register NPU: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error during NPU registration: {e}", exc_info=True)

    # Start worker threads
    logger.info(f"Starting {PARALLEL_PROCESS} worker threads")
    WORKERS = [Worker(f"WORKER_{i}") for i in range(PARALLEL_PROCESS)]
    for worker in WORKERS:
        worker.start()
    logger.info(f"All {len(WORKERS)} workers started")

    # Start background metrics polling thread
    logger.info("Starting metrics poller thread")
    metrics_thread = threading.Thread(target=start_metrics_poller, daemon=True)
    metrics_thread.start()

    logger.info("Application startup complete")
    
    yield  # --- Application is running ---
    
    # Shutdown sequence
    logger.info("Application shutdown initiated")
    
    # Stop all workers
    for worker in WORKERS:
        worker.stop()
    
    # Wait for workers to finish (with timeout)
    logger.info("Waiting for workers to finish...")
    for worker in WORKERS:
        worker.join(timeout=5)
    
    logger.info(f"NPU {NODE_ID} shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================
app = FastAPI(lifespan=lifespan, title="NPU Node Runner", version="1.0.0")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - returns basic node information and status.
    """
    with status_lock:
        current_status = status.copy()
    
    return {
        "node_id": NODE_ID,
        "port": PORT,
        "status": "active",
        "uptime": time.time() - START_TIME,
        "successful_tasks": current_status["successful_tasks"],
        "failed_tasks": current_status["failed_tasks"],
        "queued_tasks": QUEUE.qsize()
    }


@app.post("/run-node")
async def run_node(node: Node):
    """
    Queue a node for execution.
    
    Args:
        node: Node object containing code and inputs
        
    Returns:
        Success message and queue size
    """
    logger.info(f"Received node for execution: {node.node_name}, runner: {node.runner_id}")
    
    try:
        QUEUE.put_nowait(node)
        queue_size = QUEUE.qsize()
        logger.info(f"Node queued successfully. Current queue size: {queue_size}")
        
        return {
            "status": "queued",
            "node_name": node.node_name,
            "queue_size": queue_size
        }
    except Exception as e:
        logger.error(f"Failed to queue node {node.node_name}: {e}", exc_info=True)
        raise


@app.post("/log/{runner_id}")
async def add_log(runner_id: uuid.UUID, message: str):
    """
    Forward a log message to the node runner.
    
    Args:
        runner_id: UUID of the runner
        message: Log message to forward
    """
    logger.info(f"Received log request for runner {runner_id}")
    await send_npu_log(str(runner_id), message)
    return {"status": "success"}


@app.post("/result/{runner_id}")
async def result(runner_id: uuid.UUID, ret: NodeResult):
    """
    Receive and forward execution results.
    Updates task counters and forwards results to node runner.
    
    Args:
        runner_id: UUID of the runner
        ret: NodeResult object with execution results
    """
    logger.info(f"Received result for runner {runner_id}, status: {ret.status}")
    
    # Update status counters
    with status_lock:
        if ret.status == "DONE":
            status["successful_tasks"] += 1
            logger.info(f"Task succeeded. Total successful: {status['successful_tasks']}")
        else:
            status["failed_tasks"] += 1
            logger.error(f"Task failed. Total failed: {status['failed_tasks']}")
    
    # Forward result to node runner
    try:
        await send_node_result(str(runner_id), ret)
        return {"status": "forwarded"}
    except Exception as e:
        logger.error(f"Failed to forward result for runner {runner_id}: {e}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "node_id": NODE_ID,
        "uptime": time.time() - START_TIME,
        "workers_active": len([w for w in WORKERS if w.is_alive()])
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info(f"Starting NPU Node Runner")
    logger.info(f"Node ID: {NODE_ID}")
    logger.info(f"Host: {HOST}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Node Runner Address: {NODE_RUNNER_ADDR}")
    logger.info(f"Parallel Processes: {PARALLEL_PROCESS}")
    logger.info("=" * 80)
    
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")