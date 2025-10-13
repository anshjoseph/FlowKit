from node_runner.task_manager.node import Node, NodeStatus
from typing import Dict, List, Optional
from uuid import UUID
from node_runner.npu_manager.schduler import get_scheduler
from node_runner.npu import NPU
from node_runner.log import configure_logger
import asyncio
import time

logger = configure_logger(__file__)

class Manager:
    _instance: Optional["Manager"] = None

    def __new__(cls, *args, **kwargs) -> "Manager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.__active_nodes: Dict[UUID, Node] = {}
        self._initialized: bool = True
        logger.info("Manager singleton initialized")

    async def get_npu(self) -> NPU:
        logger.info("Fetching least busy NPU")
        scheduler = await get_scheduler()
        npu = NPU(await scheduler.get_next_npu())
        await npu.check_connection()
        logger.info(f"NPU {npu.npu_status.id} ready for execution")
        return npu


    def check_the_result(self, runner_id):
        while self.__active_nodes[runner_id].status not in [NodeStatus.DONE, NodeStatus.ERROR]:
            time.sleep(0.2)

    async def run_node(
        self,
        node_name: str,
        code: str,
        inputs: Dict[str, object],
        runner_id: UUID
    ) -> Node:
        logger.info(f"Creating node {node_name} with runner_id {runner_id}")
        node = Node(
            node_name=node_name,
            code_base64=code,
            inputs=inputs,
            runner_id=runner_id,
            outputs={},
            status=NodeStatus.QUEUED,
            logs=[]
        )

        logger.info(f"Preprocessing node {runner_id}")
        await node.pre_process()

        npu: NPU = await self.get_npu()

        
        self.__active_nodes[runner_id] = node
        logger.info(f"Node {runner_id} queued on NPU {npu.npu_status.id}")
        await npu.run_node(runner_id=node.runner_id, code=node.code_base64, inputs=node.inputs, node_name=node.node_name)
        self.__active_nodes[runner_id].status = NodeStatus.RUNNING

        await asyncio.to_thread(self.check_the_result, runner_id)

        final_node = self.__active_nodes.pop(runner_id)
        logger.info(f"Node {runner_id} completed with status {final_node.status}")
        return final_node

    async def retrun_hook(
        self,
        runner_id: UUID,
        nodes: List[str],
        outputs: Dict[str, object],
        message: str,
        status: str
    ):
        if self.__active_nodes.get(runner_id) == None:
            raise ValueError(f"{runner_id} is not exits") 
        logger.info(f"Node hook called for {runner_id} with status {status}")
        if runner_id not in self.__active_nodes:
            logger.error(f"Runner ID {runner_id} not found in active nodes")
            return

        self.__active_nodes[runner_id].outputs = {
            "nodes": nodes,
            "outputs": outputs,
            "status": status,
            "message": message
        }

        if status == "ERROR":
            self.__active_nodes[runner_id].status = NodeStatus.ERROR
            logger.error(f"Node {runner_id} marked as ERROR")
        elif status == "DONE":
            self.__active_nodes[runner_id].status = NodeStatus.DONE
            logger.info(f"Node {runner_id} marked as DONE")
    
    async def add_log(self,
        runner_id: UUID, log:str):
        if self.__active_nodes.get(runner_id) == None:
            raise ValueError(f"{runner_id} is not exits")  
        self.__active_nodes[runner_id].logs.append(log)
        logger.info(f"add log : {self.__active_nodes[runner_id].logs}")

# ---------------------------
# FastAPI dependency helper
# ---------------------------

_manager_instance: Optional[Manager] = None

async def get_manager() -> Manager:
    """
    Async helper to get the singleton Manager instance.
    Can be used as a FastAPI dependency.
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = Manager()
    return _manager_instance
