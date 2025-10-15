import httpx
from controlunit.config import get_config
from uuid import uuid4, UUID
from pydantic import BaseModel
from typing import List, Dict, Any
from controlunit.log import configure_logger

logger = configure_logger(__file__)

class NodeOutputs(BaseModel):
    nodes: List[str]
    outputs: Dict[str, Any]
    status: str
    message: str


class NodeExecutionData(BaseModel):
    node_name: str
    runner_id: UUID
    code: str
    status: str
    inputs: Dict[str, Any]
    logs: List[str]
    outputs: NodeOutputs


class Node:
    def __init__(self, name: str, code: str, flow_lvl: int):
        self.name = name
        self.code = code
        self.flow_lvl = flow_lvl
        logger.debug(f"Node '{self.name}' initialized at flow level {self.flow_lvl}")

    def get_code(self):
        logger.debug(f"Fetching code for node '{self.name}'")
        return self.code

    def get_flow_lvl(self):
        logger.debug(f"Fetching flow level for node '{self.name}' -> {self.flow_lvl}")
        return self.flow_lvl

    def run(self, inputs) -> NodeExecutionData:
        runner_url = get_config().node_runner
        runner_id = uuid4()
        logs = []

        payload = {
            "node_name": self.name,
            "code": self.code,
            "inputs": inputs,
            "runner_id": str(runner_id),
        }

        logs.append(f"🚀 Node '{self.name}' initialized with runner ID {runner_id}.")
        logger.info(f"Executing node '{self.name}' [runner_id={runner_id}] with inputs: {inputs}")

        try:
            logger.info(f"Sending POST to {runner_url}/nodes/add-node with payload keys: {list(payload.keys())}")
            response = httpx.post(f"{runner_url}/nodes/add-node", json=payload, timeout=50)
            response.raise_for_status()

            response_json:dict = response.json()
            logger.info(f"Response from runner received for node '{self.name}': {response_json}")

        
            logs.append("✅ Node executed successfully.")
            logger.info(f"Node '{self.name}' execution completed successfully [runner_id={runner_id}]")
            _output = NodeOutputs(
                nodes=response_json.get("outputs").get("nodes"),
                outputs=response_json.get("outputs").get("outputs"),
                status=response_json.get("outputs").get("status"),
                message=response_json.get("outputs").get("message")
            )
            return NodeExecutionData(
                node_name=self.name,
                runner_id=runner_id,
                code=self.code,
                status="success",
                inputs=inputs,
                logs=logs,
                outputs=_output,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"❌ HTTP error for node '{self.name}': {e.response.status_code} - {e.response.text}"
            logs.append(error_msg)
            logger.error(error_msg)
            return NodeExecutionData(
                node_name=self.name,
                runner_id=runner_id,
                code_base64=self.code,
                status="failed",
                inputs=inputs,
                logs=logs,
                outputs=NodeOutputs(nodes=[], outputs={}, status="error", message=error_msg),
            )

        except httpx.RequestError as e:
            error_msg = f"❌ Request failed for node '{self.name}': {e}"
            logs.append(error_msg)
            logger.error(error_msg)
            return NodeExecutionData(
                node_name=self.name,
                runner_id=runner_id,
                code_base64=self.code,
                status="failed",
                inputs=inputs,
                logs=logs,
                outputs=NodeOutputs(nodes=[], outputs={}, status="error", message=str(e)),
            )

        except Exception as e:
            error_msg = f"❌ Unexpected error in node '{self.name}': {e}"
            logs.append(error_msg)
            logger.exception(error_msg)
            return NodeExecutionData(
                node_name=self.name,
                runner_id=runner_id,
                code_base64=self.code,
                status="failed",
                inputs=inputs,
                logs=logs,
                outputs=NodeOutputs(nodes=[], outputs={}, status="error", message=str(e)),
            )

    def to_dict(self):
        logger.debug(f"Serializing node '{self.name}' to dict")
        return {
            "name": self.name,
            "code": self.code,
            "flow_lvl": self.flow_lvl
        }
