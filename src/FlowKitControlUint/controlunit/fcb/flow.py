from controlunit.fcb.node import Node
from typing import Dict
from controlunit.log import configure_logger

logger = configure_logger(__file__)

class Flow:
    def __init__(self, nodes: Dict[str, Node], curr_inp: object, curr_node: Node):
        self.nodes: Dict[str, Node] = nodes
        self.curr_inp_data = curr_inp
        self.curr_node: Node = curr_node
        logger.info(f"Flow initialized with {len(nodes)} nodes")

    def set_pointer(self, node: Node, inp_data: object):
        if self.nodes.get(node.name) is not None:
            self.curr_node = node
            self.curr_inp_data = inp_data
            logger.info(f"Pointer set to node '{node.name}' with input: {inp_data}")
        else:
            logger.error(f"Attempted to set pointer to missing node '{node.name}'")
            raise ValueError(f"Node with name '{node.name}' not present in flow")

    def get_curr_node(self):
        logger.info(f"Getting current node: {self.curr_node.name if self.curr_node else None}")
        return self.curr_node

    def get_curr_inp(self):
        logger.info(f"Getting current input data: {self.curr_inp_data}")
        return self.curr_inp_data

    def to_dict(self):
        flow_dict = {
            "nodes": {name: node.to_dict() for name, node in self.nodes.items()},
            "curr_inp_data": self.curr_inp_data,
            "curr_node": self.curr_node.to_dict() if self.curr_node else None
        }
        logger.info(f"Serialized flow to dict with {len(self.nodes)} nodes")
        return flow_dict
