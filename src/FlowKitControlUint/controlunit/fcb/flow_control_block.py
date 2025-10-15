from controlunit.fcb.flow import Flow
from controlunit.fcb.node import Node, NodeExecutionData
from typing import List, Dict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID
from controlunit.log import configure_logger
import requests
import base64
from uuid import UUID
from typing import Dict, List, Any, Optional

logger = configure_logger(__file__)


def post_trace_request(
    flow_id: UUID,
    flow_lvl: int,
    node_name: str,
    code_base64: str,
    status: str,
    inputs: Optional[Dict[str, Any]] = None,
    logs: Optional[List[str]] = None,
    outputs_nodes: Optional[List[str]] = None,
    outputs_data: Optional[Dict[str, Any]] = None,
    outputs_status: str = "SUCCESS",
    outputs_message: str = "Executed successfully",
):
    """Send a trace POST request to the FlowControl service (sync)."""

    url = f"http://127.0.0.1:9000/trace?flow_id={flow_id}&flow_lvl={flow_lvl}"

    payload = {
        "node_name": node_name,
        "runner_id": str(flow_id),
        "code_base64": code_base64,  # already base64 encoded
        "status": status,
        "inputs": inputs or {},
        "logs": logs or [],
        "outputs": {
            "nodes": outputs_nodes or [],
            "outputs": outputs_data or {},
            "status": outputs_status,
            "message": outputs_message,
        },
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.info(f"❌ Failed to send trace: {e}")
        return None


class BlockStatus(str, Enum):
    QUEUED = "QUEUED"
    START = "START"
    PAUSE = "PAUSE"
    STOP = "STOP"

class FlowControlBlock:
    def __init__(self, flow: Flow, flow_id: UUID, thread_pool: ThreadPoolExecutor, save_state_hook, stop_hook):
        self.flow: Flow = flow
        self.flow_id = flow_id
        self.node_exec_queue: List[List[Node, Dict[str, object]]] = []
        self.status: BlockStatus = BlockStatus.QUEUED
        self.thread_pool = thread_pool
        self.save_state_hook = save_state_hook
        self.stop_hook = stop_hook
        logger.info(f"FlowControlBlock {self.flow_id} initialized in QUEUED state")

    def start(self):
        logger.info(f"FlowControlBlock {self.flow_id} starting")
        self.status = BlockStatus.START
        self.exec()

    def stop(self):
        logger.info(f"FlowControlBlock {self.flow_id} stopping")
        self.status = BlockStatus.STOP
        # self.stop_hook(self.flow_id)
        

    def pause(self):
        logger.info(f"FlowControlBlock {self.flow_id} paused")
        self.status = BlockStatus.PAUSE

    def resumse(self):
        if self.status == BlockStatus.PAUSE:
            logger.info(f"FlowControlBlock {self.flow_id} resuming")
            self.status = BlockStatus.START
            self.exec()

    def _run_node(self):
        curr_node = self.flow.get_curr_node()
        curr_inp = self.flow.get_curr_inp()
        if curr_node is None:
            logger.info(f"FlowControlBlock {self.flow_id} reached end of flow")
            self.stop()
            return

        logger.info(f"Executing node '{curr_node.name}' in flow {self.flow_id}")
        try:
            result = curr_node.run(curr_inp)
            logger.info(f"Node '{curr_node.name}' executed with status '{result.status}' in flow {self.flow_id}")
            logger.info(f"Node '{curr_node.name}' outputs: {result.outputs.outputs}")
            self.exec_hook(result)
            post_trace_request(
                self.flow_id,
                curr_node.flow_lvl,
                node_name=curr_node.name,
                code_base64=curr_node.get_code(),
                status=result.status,
                inputs=curr_inp,
                logs=result.logs,
                outputs_data=result.outputs.outputs,
                outputs_nodes=result.outputs.nodes,
                outputs_status=result.outputs.status,
                outputs_message=result.outputs.message

            )
        except Exception as e:
            logger.exception(f"Exception while executing node '{curr_node.name}' in flow {self.flow_id}: {e}")
            self.status = BlockStatus.STOP
            # self.stop_hook(self.flow_id)

    def exec(self):
        if self.status in [BlockStatus.PAUSE, BlockStatus.STOP]:
            logger.debug(f"Execution halted for flow {self.flow_id} (status={self.status})")
            return
        logger.info(f"Submitting next node execution for flow {self.flow_id}")
        self.thread_pool.submit(self._run_node)

    def exec_hook(self, result: NodeExecutionData):
        logger.info(f"Processing exec_hook for node '{result.node_name}' in flow {self.flow_id}")
        _node = None
        try:
            for node_name in result.outputs.nodes:
                if self.flow.nodes.get(node_name):
                    self.node_exec_queue.append([self.flow.nodes[node_name], result.outputs.outputs])
                    logger.info(f"Queued node '{node_name}' with inputs: {result.outputs.outputs}")
                else:
                    raise ValueError(f"Node '{node_name}' not present in flow {self.flow_id}")

            if not self.node_exec_queue:
                logger.info(f"No more nodes to execute in flow {self.flow_id}, stopping")
                self.stop()
                
                return

            _node, _inputs = self.node_exec_queue.pop(0)
            logger.info(f"Setting pointer to node '{_node.name}' with inputs: {_inputs}")
            self.flow.set_pointer(_node, _inputs)

            logger.info(f"Saving state for flow {self.flow_id}")
            self.save_state_hook(self.flow_id)

            logger.info(f"Continuing execution of flow {self.flow_id}")
            self.exec()

        except Exception as e:
            self.status = BlockStatus.STOP
            logger.exception(f"Error during exec_hook for node '{_node.name if _node else 'UNKNOWN'}' in flow {self.flow_id}: {e}")
            # self.stop_hook(self.flow_id)

    def get_save_state(self):
        logger.debug(f"Generating save state for flow {self.flow_id}")
        return {
            "flow": self.flow.to_dict(),
            "flow_id": str(self.flow_id),
            "node_exec_queue": [[node.to_dict(), inp] for node, inp in self.node_exec_queue],
            "status": self.status.value
        }

    def load_from_save_state(self, state: dict):
        logger.info(f"Loading FlowControlBlock {state['flow_id']} from saved state")
        self.flow = Flow(
            nodes={name: Node(**node) for name, node in state["flow"]["nodes"].items()},
            curr_inp=state["flow"]["curr_inp_data"],
            curr_node=Node(**state["flow"]["curr_node"]) if state["flow"]["curr_node"] else None
        )
        self.flow_id = UUID(state["flow_id"])
        self.node_exec_queue = [[Node(**node), inp] for node, inp in state["node_exec_queue"]]
        self.status = BlockStatus(state["status"])
        logger.info(f"FlowControlBlock {self.flow_id} restored successfully")
