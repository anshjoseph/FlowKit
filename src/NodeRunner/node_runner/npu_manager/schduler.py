from node_runner.npu_manager.session import get_npu_session, NpuStatus, NpuSession
from typing import Optional
from uuid import UUID
from node_runner.log import configure_logger
import random

logger = configure_logger(__file__)

class NpuScheduler:
    """Scheduler that selects the NPU with the least queued tasks."""

    _instance: Optional[NpuScheduler] = None

    def __new__(cls, *args, **kwargs) -> NpuScheduler:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.session: Optional[NpuSession] = None
        self._initialized: bool = True

    async def init(self) -> NpuScheduler:
        """Initialize the NPU session singleton."""
        if not self.session:
            logger.info("Initializing NPU session in Scheduler")
            self.session = await get_npu_session()
        logger.info("NPU Scheduler initialized successfully")
        return self

    async def get_next_npu(self) -> Optional[NpuStatus]:
        """
        Select the NPU with the least queued tasks.
        If there's a tie, pick the first one.
        """
        assert self.session is not None
        npus: list[NpuStatus] = await self.session.get_all_npus()
        logger.info(npus)
        if not npus:
            logger.warning("No NPUs found in session")
            return None

        # Find NPU with minimum queued tasks
        seleted_idx = random.randint(0, len(npus)-1)
        selected_npu = npus[seleted_idx]
        
        logger.info(f"Selected NPU: {selected_npu.id} with {selected_npu.metrics.queued_tasks} queued tasks")
        return selected_npu

    async def get_next_npu_id(self) -> Optional[str]:
        """Return the ID of the NPU with least queued tasks."""
        npu = await self.get_next_npu()
        if not npu:
            logger.warning("No NPU available")
            return None
        return str(npu.id)


# ---------------------------
# Singleton helper
# ---------------------------

_scheduler: Optional[NpuScheduler] = None


async def get_scheduler() -> NpuScheduler:
    """Get or create the singleton scheduler."""
    global _scheduler
    if _scheduler is None:
        logger.info("Creating a new NPU Scheduler instance")
        _scheduler = await NpuScheduler().init()
    return _scheduler