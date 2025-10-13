from node_runner.npu_manager.session import NpuStatus
import aiohttp
import httpx
from typing import Union, List, Dict
from node_runner.log import configure_logger

logger = configure_logger(__file__)

class NPU:
    def __init__(self, npu_status: NpuStatus):
        self.npu_status: NpuStatus = npu_status

    async def check_connection(self) -> bool:
        """
        Check if the NPU is reachable via HTTP GET request.
        Returns True if status code 200, else False.
        """
        url = f"{self.npu_status.address}/"
        logger.debug(f"[NPU {self.npu_status.id}] Checking connection to {url}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        logger.info(f"[NPU {self.npu_status.id}] Connection successful ({resp.status})")
                        return True
                    else:
                        logger.warning(f"[NPU {self.npu_status.id}] Connection returned non-200: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"[NPU {self.npu_status.id}] Connection check failed: {e}", exc_info=True)
            return False

    async def run_node(self, runner_id: str, code: str, inputs: Dict[str, object], node_name: str):
        """
        Send a node execution request to the Node Runner service.
        """
        url = f"{self.npu_status.address}/run-node"
        payload = {
            "runner_id": str(runner_id),
            "code": code,
            "inputs": inputs,
            "node_name": node_name,
        }

        logger.info(f"[NPU {self.npu_status.id}] Sending node execution request — node: {node_name}, runner: {runner_id}")
        logger.debug(f"[NPU {self.npu_status.id}] Payload: {payload}")

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"[NPU {self.npu_status.id}] Node execution request succeeded — node: {node_name}")
                logger.debug(f"[NPU {self.npu_status.id}] Response data: {data}")
                return {
                    "status": "success",
                    "data": data
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"[NPU {self.npu_status.id}] HTTP error while running node {node_name}: {e.response.status_code} {e.response.text}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"HTTP error: {e.response.text}",
                }

            except httpx.RequestError as e:
                logger.error(f"[NPU {self.npu_status.id}] Request error while connecting to {url}: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Request error: {e}",
                }

            except Exception as e:
                logger.error(f"[NPU {self.npu_status.id}] Unexpected error during node run: {e}", exc_info=True)
                return {
                    "status": "error",
                    "message": f"Unexpected error: {e}",
                }
