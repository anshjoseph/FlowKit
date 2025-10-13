from pydantic import BaseModel, Field
from enum import Enum
from typing import Dict, List, Union
from base64 import b64decode, b64encode
import re
import aiohttp
from node_runner.config import get_config  # assumes get_config() returns an object with .secret_manager
from uuid import UUID

class NodeStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    ERROR = "ERROR"


class Node(BaseModel):
    node_name: str
    runner_id : UUID # its a unique id for each node runner task
    code_base64: str
    status: NodeStatus
    inputs: Dict[str, object]
    logs: List[str] = Field(default_factory=list)
    outputs: Dict[str, object]

    def decode_code(self) -> str:
        """Decode Base64-encoded code."""
        return b64decode(self.code_base64.encode()).decode("utf-8")

    def encode_code(self, code: str) -> None:
        """Encode plain code into Base64."""
        self.code_base64 = b64encode(code.encode()).decode()

    async def resolve_secrets(self, text: str) -> str:
        """
        Find and replace secret placeholders like {{{secret::KEY}}}
        with their real values from the Secret Manager server.
        Raise ValueError if any secret is missing or fails to fetch.
        """
        pattern = re.compile(r"\{\{\{secret::(.*?)\}\}\}")
        matches = pattern.findall(text)

        if not matches:
            return text

        async with aiohttp.ClientSession() as session:
            for key in matches:
                url = f"{get_config().secret_manager}/get/{key}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ValueError(f"Failed to fetch secret: {key}")
                    data = await resp.json()
                    value = data.get("value")
                    if not value:
                        raise ValueError(f"Secret not found or empty: {key}")
                    text = text.replace("{{{secret::"+key+"}}}", value)
        return text

    async def pre_process(self):
        """
        Decode code, resolve secrets inside it, and re-encode the final code.
        """
        decoded = self.decode_code()
        resolved = await self.resolve_secrets(decoded)
        self.encode_code(resolved)

    async def add_log(self, message:str):
        self.logs.append(message)