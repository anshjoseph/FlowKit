from fastapi import APIRouter
from pydantic import BaseModel
from uuid import UUID
from typing import Dict, Union
from node_runner.log import configure_logger
from node_runner.task_manager.manager import get_manager


logger = configure_logger(__file__)
node_router = APIRouter(
    prefix="/nodes",
    tags=["Node Management"]
)


# DTOs
class NodeReq(BaseModel):
    node_name : str
    code : str
    inputs : Dict[str, object]
    runner_id : UUID

@node_router.post("/add-node")
async def add_node(node : NodeReq):
    
    node = await (await get_manager()).run_node(node_name=node.node_name, code=node.code, inputs=node.inputs, runner_id=node.runner_id)
    return node