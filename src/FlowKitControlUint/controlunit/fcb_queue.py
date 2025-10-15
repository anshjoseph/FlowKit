from typing import Dict
from uuid import UUID, uuid4
from concurrent.futures import ThreadPoolExecutor
import pymongo

from controlunit.fcb.flow_control_block import FlowControlBlock
from controlunit.fcb.flow import Flow
from controlunit.fcb.node import Node
from controlunit.log import configure_logger
from controlunit.config import get_config

logger = configure_logger(__file__)


class FlowControlBlockQueue:
    def __init__(self):
        self.Blocks: Dict[UUID, FlowControlBlock] = {}
        self.__threadpool = ThreadPoolExecutor(20)
        self.__mongoclient = pymongo.MongoClient(get_config().mongodb)
        self.__db = self.__mongoclient[get_config().db_name]
        self.__collection = self.__db[get_config().collection]
        logger.info("Initialized FlowControlBlockQueue with MongoDB connection (sync)")

    def recover_from_storage(self):
        """Recover all FlowControlBlocks from MongoDB and start them."""
        logger.info("Starting recovery of FlowControlBlocks from MongoDB")
        try:
            for block in self.__collection.find({}):
                try:
                    flow_dict = block["state"]

                    nodes = {
                        name: Node(
                            node_data["name"],
                            node_data["code"],
                            node_data.get("flow_lvl"),
                        )
                        for name, node_data in flow_dict["nodes"].items()
                    }

                    curr_node_data = flow_dict.get("curr_node")
                    curr_node = (
                        Node(
                            curr_node_data["name"],
                            curr_node_data["code"],
                            curr_node_data.get("flow_lvl"),
                        )
                        if curr_node_data
                        else None
                    )

                    flow = Flow(nodes, flow_dict.get("curr_inp_data"), curr_node)
                    flow_id = UUID(block["flow_id"])

                    fcb = FlowControlBlock(
                        flow, flow_id, self.__threadpool, self.save_state_hook, self.stop_hook
                    )
                    self.Blocks[flow_id] = fcb
                    fcb.start()

                    logger.info(f"✅ Recovered and started FCB with id {flow_id} from storage")

                except Exception as e:
                    logger.error(f"❌ Failed to recover FCB from block {block}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"❌ Error fetching blocks from MongoDB: {e}", exc_info=True)

    def save_state_hook(self, flow_id: UUID):
        """Save the current flow state to MongoDB."""
        try:
            if flow_id not in self.Blocks:
                raise ValueError(f"Flow {flow_id} not found in Blocks")

            flow_state = self.Blocks[flow_id].flow.to_dict()

            self.__collection.update_one(
                {"flow_id": str(flow_id)},
                {"$set": {"state": flow_state}},
                upsert=True,
            )

            logger.info(f"💾 State of flow {flow_id} saved to storage")

        except Exception as e:
            logger.error(f"❌ Error saving flow {flow_id} state: {e}", exc_info=True)

    def stop_hook(self, flow_id: UUID):
        """Stop and remove the FCB from MongoDB and memory."""
        try:
            fcb = self.Blocks.get(flow_id)
            if fcb is None:
                raise ValueError(f"Flow {flow_id} not found")

            fcb.stop()
            self.Blocks.pop(flow_id, None)
            self.__collection.delete_one({"flow_id": str(flow_id)})

            logger.info(f"🧹 Flow {flow_id} stopped and removed from storage")

        except Exception as e:
            logger.error(f"❌ Error in stop_hook for flow {flow_id}: {e}", exc_info=True)

    def add_fcb(self, flow: Flow) -> UUID:
        """Add a new FlowControlBlock."""
        flow_id = uuid4()
        fcb = FlowControlBlock(flow, flow_id, self.__threadpool, self.save_state_hook, self.stop_hook)
        self.Blocks[flow_id] = fcb
        logger.info(f"➕ Added new FlowControlBlock with id {flow_id}")
        return flow_id

    def start_fcb(self, flow_id: UUID):
        fcb = self.Blocks.get(flow_id)
        if fcb is None:
            raise ValueError(f"Flow {flow_id} not found")
        fcb.start()
        logger.info(f"▶️ Started FlowControlBlock {flow_id}")

    def stop_fcb(self, flow_id: UUID):
        fcb = self.Blocks.get(flow_id)
        if fcb is None:
            raise ValueError(f"Flow {flow_id} not found")

        fcb.stop()
        self.Blocks.pop(flow_id, None)
        self.__collection.delete_one({"flow_id": str(flow_id)})
        logger.info(f"🛑 Flow {flow_id} stopped and deleted")

    def pause_fcb(self, flow_id: UUID):
        fcb = self.Blocks.get(flow_id)
        if fcb is None:
            raise ValueError(f"Flow {flow_id} not found")
        fcb.pause()
        logger.info(f"⏸ Paused FlowControlBlock {flow_id}")

    def resume_fcb(self, flow_id: UUID):
        fcb = self.Blocks.get(flow_id)
        if fcb is None:
            raise ValueError(f"Flow {flow_id} not found")
        fcb.resume()
        logger.info(f"▶️ Resumed FlowControlBlock {flow_id}")

    def clean_up(self):
        """Stop all flows and close resources."""
        logger.info("Cleaning up all FlowControlBlocks")
        for flow_id, fcb in list(self.Blocks.items()):
            try:
                fcb.stop()
                logger.info(f"🛑 Stopped FlowControlBlock {flow_id} during cleanup")
            except Exception:
                pass
            self.Blocks.pop(flow_id, None)

        self.__threadpool.shutdown(wait=False)
        self.__mongoclient.close()
        logger.info("🧽 Cleaned up FlowControlBlockQueue resources")
