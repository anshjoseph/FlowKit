from fastapi import FastAPI, HTTPException, Query
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import os
from uuid import uuid4, UUID
from pydantic import BaseModel
from typing import List, Dict, Any

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv(".env")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 9000))
MONGODB = os.getenv("MONGODB", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "FlowKit")
COLLECTION = os.getenv("COLLECTION", "traces")

# -----------------------------
# Models
# -----------------------------
class NodeOutputs(BaseModel):
    nodes: List[str]
    outputs: Dict[str, Any]
    status: str
    message: str


class NodeExecutionData(BaseModel):
    node_name: str
    runner_id: UUID
    code_base64: str
    status: str
    inputs: Dict[str, Any]
    logs: List[str]
    outputs: NodeOutputs


# -----------------------------
# App and MongoDB setup
# -----------------------------
app = FastAPI(title="FlowKit Trace Server")
client: AsyncIOMotorClient = None
db = None
collection = None

# Dictionary to track the sequence count for each flow
flow_registry: Dict[str, int] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db, collection
    client = AsyncIOMotorClient(MONGODB)
    db = client[DB_NAME]
    collection = db[COLLECTION]
    print(f"✅ Connected to MongoDB: {MONGODB}")
    yield
    client.close()
    print("🛑 MongoDB connection closed.")


app.router.lifespan_context = lifespan


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {
        "message": "FlowKit Trace Server running",
        "tracked_flows": flow_registry,
    }


@app.post("/trace")
async def save_trace(
    data: NodeExecutionData,
    flow_id: UUID = Query(..., description="Unique Flow ID"),
    flow_lvl: int = Query(..., description="Execution level within the flow"),
):
    """
    Save node execution trace to MongoDB.
    Maintain and store the current execution sequence for each flow.
    """
    fid = str(flow_id)
    record = data.dict()

    # Assign MongoDB _id and convert UUID fields
    record["_id"] = str(uuid4())
    record["runner_id"] = str(record["runner_id"])
    record["flow_id"] = fid
    record["flow_lvl"] = flow_lvl

    # Increment or initialize sequence count for this flow
    flow_registry[fid] = flow_registry.get(fid, 0) + 1
    record["current_sequence"] = flow_registry[fid]

    # Save to MongoDB
    await collection.insert_one(record)

    return {
        "message": "Trace saved successfully",
        "trace_id": record["_id"],
        "flow_id": fid,
        "flow_lvl": flow_lvl,
        "current_sequence": flow_registry[fid],
    }


@app.get("/trace/{runner_id}")
async def get_trace(runner_id: UUID):
    """Retrieve all traces for a specific runner."""
    traces = await collection.find({"runner_id": str(runner_id)}).to_list(length=None)
    if not traces:
        raise HTTPException(status_code=404, detail="No traces found for this runner_id")
    return {"runner_id": runner_id, "traces": traces}


@app.get("/flow/{flow_id}")
async def get_flow_traces(flow_id: UUID):
    """
    Retrieve all traces for a specific flow, ordered by current_sequence
    (the real path of execution).
    """
    traces = await collection.find({"flow_id": str(flow_id)}).sort("current_sequence", 1).to_list(length=None)
    if not traces:
        raise HTTPException(status_code=404, detail="No traces found for this flow_id")

    count = flow_registry.get(str(flow_id), len(traces))
    path = [trace["node_name"] for trace in traces]

    return {
        "flow_id": str(flow_id),
        "total_nodes": count,
        "execution_path": path,
        "traces": traces,
    }


@app.get("/flows")
async def get_all_flows():
    """Get all registered flows and their execution counts."""
    return {"total_flows": len(flow_registry), "flows": flow_registry}


@app.delete("/trace/{trace_id}")
async def delete_trace(trace_id: str):
    """Delete a trace record by its ID."""
    result = await collection.delete_one({"_id": trace_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {"message": "Trace deleted successfully"}


@app.get("/traces")
async def get_all_traces(limit: int = 20):
    """Get recent traces (default limit 20)."""
    traces = await collection.find().sort("_id", -1).to_list(length=limit)
    return {"count": len(traces), "traces": traces}


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
