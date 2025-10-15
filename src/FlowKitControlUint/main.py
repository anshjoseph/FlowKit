from controlunit.config import get_config
from controlunit.fcb.flow import Flow
from controlunit.fcb.flow_control_block import FlowControlBlock
from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException, Request
from typing import Dict
import uvicorn
from controlunit.log import configure_logger
from controlunit.fcb.node import Node
from controlunit.fcb_queue import FlowControlBlockQueue
from contextlib import asynccontextmanager
import asyncio
from pydantic import BaseModel


logger = configure_logger(__file__)

# DTOs
class NodeDTO(BaseModel):
    name: str
    code: str
    flow_lvl: int

class AddFCBRequest(BaseModel):
    nodes: Dict[str, NodeDTO]
    curr_inp: Dict[str, object]
    curr_node: NodeDTO


FCB_QUEUE: FlowControlBlockQueue = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global FCB_QUEUE
    logger.info("Starting FlowKit Control Unit lifespan")
    get_config()  # Ensure config is loaded
    FCB_QUEUE = FlowControlBlockQueue()
    FCB_QUEUE.recover_from_storage()
    logger.info("Recovered FCB_QUEUE from storage")
    yield
    FCB_QUEUE.clean_up()
    logger.info("Cleaned up FCB_QUEUE and shutting down")

app = FastAPI(title="FlowKit Control Unit", version="0.1.0", lifespan=lifespan)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
    return response

@app.get("/health", tags=["Health"])
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "ok"}

@app.post("/fcb/add", tags=["Flow Control Block"])
async def add_fcb(flow: AddFCBRequest):
    logger.info(f"Add FCB request received with nodes: {list(flow.nodes.keys())}")
    try:
        _flow = Flow(
            nodes={name: Node(node_data.name, node_data.code, node_data.flow_lvl) for name, node_data in flow.nodes.items()},
            curr_inp=flow.curr_inp,
            curr_node=Node(flow.curr_node.name, flow.curr_node.code, flow.curr_node.flow_lvl) if flow.curr_node else None
        )
        id = FCB_QUEUE.add_fcb(_flow)
        FCB_QUEUE.start_fcb(id)
        
        logger.info(f"Flow Control Block added successfully with ID: {id}")
        return {"message": "Flow Control Block added successfully.", "flow_id": str(id)}
    except Exception as e:
        logger.error(f"Error adding Flow Control Block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to add Flow Control Block.")

@app.post("/fcb/{flow_id}/pause", tags=["Flow Control Block"])
async def pause_fcb(flow_id: UUID):
    logger.info(f"Pause FCB request received for ID: {flow_id}")
    try:
        FCB_QUEUE.pause_fcb(flow_id)
        logger.info(f"Flow Control Block {flow_id} paused successfully")
        return {"message": f"Flow Control Block {flow_id} paused successfully."}
    except ValueError as ve:
        logger.error(f"Error pausing Flow Control Block: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error pausing Flow Control Block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to pause Flow Control Block.")

@app.post("/fcb/{flow_id}/resume", tags=["Flow Control Block"])
async def resume_fcb(flow_id: UUID):
    logger.info(f"Resume FCB request received for ID: {flow_id}")
    try:
        FCB_QUEUE.resume_fcb(flow_id)
        logger.info(f"Flow Control Block {flow_id} resumed successfully")
        return {"message": f"Flow Control Block {flow_id} resumed successfully."}
    except ValueError as ve:
        logger.error(f"Error resuming Flow Control Block: {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error resuming Flow Control Block: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resume Flow Control Block.")

if __name__ == "__main__":
    logger.info(f"Starting FastAPI app at {get_config().host}:{get_config().port}")
    uvicorn.run(app, host=get_config().host, port=get_config().port)
