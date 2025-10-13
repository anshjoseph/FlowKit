from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Union, Literal
from uuid import UUID
from node_runner.npu_manager.session import get_npu_session, NpuMetrics
from node_runner.log import configure_logger
from node_runner.task_manager.manager import get_manager, Manager

logger = configure_logger(__file__)

# Router setup
npu_router = APIRouter(
    prefix="/npu",
    tags=["NPU Management"]
)

# ---------------------------
# DTOs
# ---------------------------

class AddNpuReq(BaseModel):
    address: str
    id: UUID

class NpuMatex(BaseModel):
    uptime: float
    successful_tasks: int
    failed_tasks: int
    queued_tasks: int

class NodeResult(BaseModel):
    nodes: List[str]
    outputs: Dict[str, Union[str, int, float]]
    message: str
    status: Literal["DONE", "ERROR"]


# ---------------------------
# Routes
# ---------------------------

@npu_router.post("/add")
async def add_npu(add_npu_request: AddNpuReq, npu_session=Depends(get_npu_session)):
    """
    Register a new NPU node with its address and UUID.
    """
    logger.info(f"[NPU ADD] Adding new NPU: {add_npu_request.id} at {add_npu_request.address}")
    try:
        result = await npu_session.add_npu(
            npu_id=add_npu_request.id,
            addr=add_npu_request.address
        )
        logger.info(f"[NPU ADD] NPU {add_npu_request.id} added successfully")
        return result
    except ValueError as e:
        logger.error(f"[NPU ADD] Failed to add NPU {add_npu_request.id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@npu_router.post("/pool/{npu_id}")
async def update_metrics(npu_id: UUID, metrics: NpuMatex, npu_session=Depends(get_npu_session)):
    """
    Update NPU metrics and reset its timeout timer.
    """
    logger.info(f"[NPU METRICS] Updating metrics for NPU {npu_id}: {metrics.dict()}")
    try:
        result = await npu_session.update_metrics(
            npu_id=npu_id,
            metrics=NpuMetrics(
                uptime=metrics.uptime,
                successful_tasks=metrics.successful_tasks,
                failed_tasks=metrics.failed_tasks,
                queued_tasks=metrics.queued_tasks,
            ),
        )
        logger.info(f"[NPU METRICS] Metrics updated for NPU {npu_id}")
        return result
    except ValueError as e:
        logger.error(f"[NPU METRICS] Failed to update metrics for NPU {npu_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@npu_router.get("/all")
async def get_all_npus(npu_session=Depends(get_npu_session)):
    """
    Get all registered NPUs and their status.
    """
    npus = await npu_session.get_all_npus()
    logger.info(f"[NPU GET ALL] Fetched {len(npus)} NPUs")
    return {"count": len(npus), "npus": npus}


@npu_router.post("/log/{runner_id}")
async def add_logs(runner_id: UUID, log: str, manager: Manager = Depends(get_manager)):
    """
    Add a log entry for a running node.
    """
    try:
        await manager.add_log(runner_id, log)
        logger.info(f"[NODE LOG] Added log for runner {runner_id}: {log}")
        return Response(status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"[NODE LOG] Failed to add log for runner {runner_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@npu_router.post("/result/{runner_id}")
async def return_node(runner_id: UUID, ret: NodeResult, manager: Manager = Depends(get_manager)):
    """
    Callback for node completion results.
    """
    try:
        await manager.retrun_hook(
            runner_id,
            nodes=ret.nodes,
            outputs=ret.outputs,
            message=ret.message,
            status=ret.status
        )
        logger.info(f"[NODE RESULT] Node {runner_id} completed with status {ret.status}")
        return Response(status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"[NODE RESULT] Failed to process node {runner_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
