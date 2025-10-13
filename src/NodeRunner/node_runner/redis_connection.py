import redis.asyncio as aioredis
from node_runner.config import get_config
from node_runner.log import configure_logger


logger = configure_logger(__file__)

redis_client: aioredis.Redis = None

def get_redis() -> aioredis.Redis:
    """
    Lazy-initialize a global Redis client using config from .env.
    """
    global redis_client
    if redis_client is None:
        cfg = get_config()
        redis_client = aioredis.Redis(
            host=cfg.redis_host,
            port=cfg.redis_port,
            db=0,
            decode_responses=True  # store strings instead of bytes
        )
    return redis_client
