from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(".env")


class Config(BaseModel):
    port: int
    host: str
    redis_host: str
    redis_port: int
    secret_manager : str


config: Config = None


def get_config():
    global config
    if config is None:
        config = Config(
            port=int(os.getenv("PORT", 8500)),
            host=os.getenv("HOST", "0.0.0.0"),
            redis_host=os.getenv("REDIS_HOST", "0.0.0.0"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            secret_manager=os.getenv("SECRET_MANAGER")
        )
    return config
