import json
from base64 import b64encode

# Define your nodes
START_NODE = """from flowkit.node import Node
from flowkit.log import Logger

node = Node()
logger = Logger(node)

async def main():
    # nodes, output, message
    inputs = node.get_inputs()
    return ["node1"], {"a":1, "b":2}, "run successfully"

node.register_main(main)
node.run()
"""

NODE_1 = """from flowkit.node import Node
from flowkit.log import Logger

node = Node()
logger = Logger(node)

async def main():
    # nodes, output, message
    inputs = node.get_inputs()
    ret = inputs["a"] + inputs["b"]
    return [], {"out": ret}, "run successfully"

node.register_main(main)
node.run()
"""

# Helper function to encode node code to base64
def encode_code(code_str: str) -> str:
    return b64encode(code_str.encode("utf-8")).decode("utf-8")

# Build flow dictionary
flow = {
    "nodes": {
        "start": {
            "name": "start",
            "code": encode_code(START_NODE),
            "flow_lvl": 1
        },
        "node1": {
            "name": "node1",
            "code": encode_code(NODE_1),
            "flow_lvl": 2
        }
    },
    "curr_inp": {},
    "curr_node": {
        "name": "start",
        "code": encode_code(START_NODE),
        "flow_lvl": 1
    }
}

# Save flow as JSON file
with open("flow.json", "w", encoding="utf-8") as f:
    json.dump(flow, f, indent=4)

print("flow.json saved successfully!")
