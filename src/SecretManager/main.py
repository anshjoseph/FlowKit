from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import uvicorn
from contextlib import asynccontextmanager
from log import configure_logger  # your custom logger

# Setup custom logger
logger = configure_logger(__file__)

# Load environment variables
load_dotenv(".env")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))  # safe port
MONGODB = os.getenv("MONGODB", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FlowKit")
COLLECTION = os.getenv("COLLECTION", "secrets")

# Global MongoDB objects
client: AsyncIOMotorClient = None
db = None
col = None

# Pydantic model
class KVItem(BaseModel):
    key: str
    value: str

# Lifespan context for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, col
    try:
        client = AsyncIOMotorClient(MONGODB, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        logger.info(f"✅ Connected to MongoDB at {MONGODB}")
        db = client[DB_NAME]
        col = db[COLLECTION]
        yield
    except Exception as e:
        logger.error(f"❌ Could not connect to MongoDB: {e}")
        yield  # still start FastAPI so you can see error
    finally:
        if client:
            client.close()
            logger.info("MongoDB connection closed")

# Initialize FastAPI with lifespan
app = FastAPI(title="FlowKit Key-Value Server", lifespan=lifespan)

# Routes
@app.post("/set")
async def set_value(item: KVItem):
    result = await col.update_one({"key": item.key}, {"$set": {"value": item.value}}, upsert=True)
    logger.info(f"Set key: {item.key}")
    return {"ok": True, "key": item.key, "value": item.value}


@app.get("/get/{key}")
async def get_value(key: str):
    doc = await col.find_one({"key": key})
    if not doc:
        logger.warning(f"Key not found: {key}")
        raise HTTPException(status_code=404, detail="Key not found")
    logger.info(f"Get key: {key}")
    return {"key": key, "value": doc["value"]}


@app.delete("/delete/{key}")
async def delete_value(key: str):
    res = await col.delete_one({"key": key})
    if res.deleted_count == 0:
        logger.warning(f"Delete failed, key not found: {key}")
        raise HTTPException(status_code=404, detail="Key not found")
    logger.info(f"Deleted key: {key}")
    return {"ok": True, "deleted": key}


@app.get("/keys")
async def list_keys():
    keys = []
    async for doc in col.find({}, {"key": 1, "_id": 0}):
        keys.append(doc["key"])
    logger.info(f"Listing all keys: {keys}")
    return {"keys": keys}


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
