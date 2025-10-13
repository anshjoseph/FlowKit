from __future__ import annotations
from pydantic import BaseModel
from node_runner.redis_connection import get_redis
from redis.asyncio import Redis
from uuid import UUID
from typing import Optional, List
import json
import asyncio
import time
from node_runner.log import configure_logger

logger = configure_logger(__file__)

# ---------------------------
# Pydantic Models
# ---------------------------

class NpuMetrics(BaseModel):
    uptime: float = 0.0
    successful_tasks: int = 0
    failed_tasks: int = 0
    queued_tasks: int = 0

class NpuStatus(BaseModel):
    id: UUID
    address: str
    status: str = "idle"
    last_seen: float = time.time()
    metrics: NpuMetrics = NpuMetrics()

# ---------------------------
# Singleton NPU Session
# ---------------------------

class NpuSession:
    _instance: Optional[NpuSession] = None

    def __new__(cls, *args, **kwargs) -> NpuSession:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, expiry_seconds: int = 10) -> None:
        if getattr(self, "_initialized", False):
            return
        self.redis: Optional[Redis] = None
        self.expiry_seconds: int = expiry_seconds
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._initialized: bool = True

    async def init(self) -> NpuSession:
        if self.redis is None:
            logger.info("Initializing Redis connection for NPU session")
            self.redis = await get_redis()
        await self.start_cleanup_loop()
        logger.info("NPU session initialized successfully")
        return self

    # ---------------------------
    # Core Methods
    # ---------------------------

    async def add_npu(self, npu_id: UUID, addr: str) -> NpuStatus:
        assert self.redis is not None
        key = f"npu:{npu_id}"
        if await self.redis.exists(key):
            logger.error(f"NPU {npu_id} already exists")
            raise ValueError(f"NPU {npu_id} already exists")

        npu = NpuStatus(id=npu_id, address=addr)
        await self.redis.hset(
            key,
            mapping={
                "id": str(npu.id),
                "address": npu.address,
                "status": npu.status,
                "last_seen": str(npu.last_seen),
                "metrics": npu.metrics.json(),
            },
        )
        await self.redis.sadd("npu:pool", str(npu_id))
        logger.info(f"Added new NPU {npu_id} at address {addr}")
        return npu

    async def update_metrics(self, npu_id: UUID, metrics: NpuMetrics) -> NpuStatus:
        assert self.redis is not None
        key = f"npu:{npu_id}"
        if not await self.redis.exists(key):
            logger.error(f"NPU {npu_id} not found when updating metrics")
            raise ValueError(f"NPU {npu_id} not found (maybe expired)")

        await self.redis.hset(
            key,
            mapping={
                "metrics": metrics.json(),
                "last_seen": str(time.time()),
            },
        )
        logger.info(f"Updated metrics for NPU {npu_id}: {metrics.dict()}")
        data = await self.redis.hgetall(key)
        return self._parse_npu_status(data)

    async def get_all_npus(self) -> List[NpuStatus]:
        assert self.redis is not None
        npu_ids = await self.redis.smembers("npu:pool")
        npus: List[NpuStatus] = []

        for nid in npu_ids:
            nid_str = nid.decode() if isinstance(nid, bytes) else str(nid)
            data = await self.redis.hgetall(f"npu:{nid_str}")
            if not data:
                continue
            npus.append(self._parse_npu_status(data))

        logger.info(f"Fetched {len(npus)} NPUs from session")
        return npus

    async def get_npu_by_id(self, npu_id: UUID) -> NpuStatus:
        assert self.redis is not None
        key = f"npu:{npu_id}"
        data = await self.redis.hgetall(key)
        if not data:
            logger.error(f"NPU {npu_id} not found")
            raise ValueError(f"NPU {npu_id} not found")
        logger.info(f"Fetched NPU {npu_id}")
        return self._parse_npu_status(data)

    async def cleanup_inactive(self) -> None:
        assert self.redis is not None
        now = time.time()
        npu_ids = await self.redis.smembers("npu:pool")

        for nid in npu_ids:
            nid_str = nid.decode() if isinstance(nid, bytes) else str(nid)
            key = f"npu:{nid_str}"
            last_seen_raw = await self.redis.hget(key, "last_seen")
            if not last_seen_raw:
                continue
            try:
                last_seen = float(last_seen_raw)
                if now - last_seen > self.expiry_seconds:
                    await self.redis.delete(key)
                    await self.redis.srem("npu:pool", nid_str)
                    logger.info(f"Removed inactive NPU {nid_str}")
            except Exception as e:
                logger.error(f"Cleanup error for NPU {nid_str}: {e}")

    async def start_cleanup_loop(self, interval: int = 1) -> None:
        if self._cleanup_task and not self._cleanup_task.done():
            return

        async def _loop() -> None:
            while True:
                await self.cleanup_inactive()
                await asyncio.sleep(interval)

        self._cleanup_task = asyncio.create_task(_loop())
        logger.info("Started NPU cleanup loop")

    # ---------------------------
    # Helper Methods
    # ---------------------------

    def _parse_npu_status(self, data: dict) -> NpuStatus:
        metrics_dict = json.loads(data.get("metrics", "{}"))
        logger.info(f"data : {metrics_dict}")
        metrics = NpuMetrics(**metrics_dict)

        return NpuStatus(
            id=UUID(data["id"]),
            address=data["address"],
            status=data.get("status", "idle"),
            last_seen=float(data.get("last_seen", time.time())),
            metrics=metrics,
        )


# ---------------------------
# Singleton helper
# ---------------------------

_npu_session: Optional[NpuSession] = None

async def get_npu_session() -> NpuSession:
    global _npu_session
    if _npu_session is None:
        logger.info("Creating new NPU session singleton")
        _npu_session = await NpuSession().init()
    return _npu_session
