from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv(".env")

class Config(BaseModel):
    mongodb:str
    db_name:str
    node_runner:str
    trace_service_addr:str
    collection:str
    host:str
    port:int


_config:Config= None


def get_config():
    global _config
    if _config == None:
        _config = Config(
            mongodb=os.getenv("MONGODB"),
            db_name=os.getenv("DB_NAME"),
            node_runner=os.getenv("NODE_RUNNER_ADDR"),
            collection=os.getenv("COLLECTION", "FCB"),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", 9500)),
            trace_service_addr=os.getenv("TRACE_SERVICE_ADDR", "http://127.0.0.1:9000")
        )
    return _config