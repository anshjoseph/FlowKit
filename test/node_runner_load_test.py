import httpx
import base64
import json
import asyncio
from uuid import uuid4
import time

BASE_URL = "http://127.0.0.1:8500"


async def add_node_async(client: httpx.AsyncClient, node_name: str, code: str, inputs: dict):
    encoded_code = base64.b64encode(code.encode()).decode()

    payload = {
        "node_name": node_name,
        "code": encoded_code,
        "inputs": inputs,
        "runner_id": str(uuid4()),
    }

    try:
        response = await client.post(f"{BASE_URL}/nodes/add-node", json=payload, timeout=50)
        response.raise_for_status()
        print(f"✅ Node added successfully [{node_name}]")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def main():
    code = """
from flowkit.node import Node
from flowkit.log import Logger

node = Node()
logger = Logger(node)

key = "{{{secret::OPENAI_KEY}}}"  # load secret key from secret manager
async def main():
    inputs = node.get_inputs()
    ret = inputs["a"] + inputs["b"]
    for i in range(10):
        await logger.info("hola")
    await logger.info(key)
    return [], {"out": ret, "key": key}, "run successfully"
node.register_main(main)
node.run()
"""

    async with httpx.AsyncClient() as client:
        tasks = [
            add_node_async(client, f"example_node_{i}", code, {"a": i, "b": i * 2})
            for i in range(50)
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()
    asyncio.run(main())
    print(f"⏱️ Total time: {time.time() - start:.2f}s")
