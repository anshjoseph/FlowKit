import httpx
import base64
import json
from uuid import uuid4
import time

BASE_URL = "http://127.0.0.1:8500"


def add_node(node_name: str, code: str, inputs: dict):
    # Encode Python code to base64
    encoded_code = base64.b64encode(code.encode()).decode()

    payload = {
        "node_name": node_name,
        "code": encoded_code,
        "inputs": inputs,
        "runner_id": str(uuid4()),
    }

    try:
        response = httpx.post(f"{BASE_URL}/nodes/add-node", json=payload, timeout=50)
        response.raise_for_status()
        print("✅ Node added successfully:")
        print(json.dumps(response.json(), indent=2))
    except httpx.HTTPError as e:
        print(f"❌ HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    code = """
from flowkit.node import Node
from flowkit.log import Logger
import openai

node = Node()
logger = Logger(node)

key = "{{{secret::OPENAI_KEY}}}"
async def main():
    # nodes, output, message
    inputs = node.get_inputs()
    ret = inputs["a"] + inputs["b"]
    for i in range(10):
        await logger.info("hola")
    # await logger.info(key)
    return ["node2"], {"out":ret , "key":key}, "run succefully"
node.register_main(main)
node.run()

"""
    _s = time.time()
    add_node(
        node_name="example_node",
        code=code,
        inputs={"a": 5, "b": 10}
    )
    print(time.time()-_s)
