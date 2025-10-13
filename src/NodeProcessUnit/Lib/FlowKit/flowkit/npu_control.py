import httpx
from typing import List, Dict, Union, Optional
from pydantic import BaseModel, Field
from typing_extensions import Literal
import asyncio


class NodeResult(BaseModel):
    """Data model for node execution results."""
    nodes: List[str] = Field(description="List of downstream nodes to execute after this node")
    outputs: Dict[str, Union[str, int, float]] = Field(description="Output data produced by this node")
    message: str = Field(description="Status message or error description")
    status: Literal["DONE", "ERROR"] = Field(description="Execution status: DONE for success, ERROR for failure")


class NpuControl:
    """NPU Control client for distributed workflow communication."""
    
    DONE = "DONE"
    ERROR = "ERROR"
    SUCCESS_STATUSES = {200, 201}

    def __init__(self, node, timeout: float = 10.0, max_retries: int = 1):
        self.node = node
        self.timeout = timeout
        # Keep persistent client for connection pooling
        self.client = httpx.AsyncClient(timeout=self.timeout)
        print(f"[NpuControl] Initialized for {node.node_name}")

    def _safe_print(self, message: str):
        """Safely print messages with encoding handling."""
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('ascii', errors='replace').decode('ascii'))

    async def log(self, message: str, retry: bool = True) -> bool:
        """Send log message to NPU control server - FAST, NO RETRY."""
        url = f"{self.node.self_addr}/log/{self.node.get_id()}"
        
        try:
            response = await self.client.post(
                url, 
                params={"message": message}, 
                headers={"accept": "application/json"}
            )
            return response.status_code in self.SUCCESS_STATUSES
        except Exception:
            return False

    async def result(
        self,
        nodes: List[str],
        outputs: Dict[str, Union[str, int, float]],
        message: str,
        status: str,
        retry: bool = True,
    ) -> bool:
        """Send node execution result to NPU control server - FAST, NO RETRY."""
        url = f"{self.node.self_addr}/result/{self.node.get_id()}"
        
        try:
            payload = NodeResult(nodes=nodes, outputs=outputs, message=message, status=status)
        except Exception as e:
            self._safe_print(f"[RESULT] Invalid payload: {type(e).__name__}")
            return False

        try:
            response = await self.client.post(
                url,
                json=payload.dict(),
                headers={"accept": "application/json", "content-type": "application/json"}
            )
            
            if response.status_code in self.SUCCESS_STATUSES:
                self._safe_print(f"[RESULT] Success -> Next nodes: {nodes}")
                return True
            
            self._safe_print(f"[RESULT] FAILED - status {response.status_code}")
            return False
                
        except Exception as e:
            self._safe_print(f"[RESULT] Error: {type(e).__name__}")
            return False

    async def health_check(self) -> bool:
        """Check if NPU control server is reachable."""
        try:
            response = await self.client.get(
                self.node.self_addr, 
                headers={"accept": "application/json"}
            )
            is_healthy = response.status_code < 500
            self._safe_print(f"[HEALTH] {'OK' if is_healthy else 'FAILED'} (status: {response.status_code})")
            return is_healthy
        except Exception as e:
            self._safe_print(f"[HEALTH] Unreachable: {type(e).__name__}")
            return False

    async def close(self):
        """Close the persistent HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()