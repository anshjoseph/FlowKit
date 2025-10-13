from fastapi import FastAPI
from node_runner.router.npu_route import npu_router
from node_runner.router.node_route import node_router
import uvicorn
from node_runner.config import get_config
from node_runner.npu_manager.session import get_npu_session
from node_runner.npu_manager.schduler import get_scheduler
from contextlib import asynccontextmanager
from node_runner.redis_connection import get_redis
from node_runner.task_manager.manager import get_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize and clean up shared resources such as Redis,
    NPU session manager, and Scheduler.
    """
    get_redis()
    await get_npu_session()
    await get_scheduler()
    await get_manager()
    yield
    

app = FastAPI(lifespan=lifespan)

# Routers
app.include_router(npu_router)
app.include_router(node_router)

if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        app,
        host=config.host,
        port=config.port
    )
