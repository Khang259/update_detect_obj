import logging
from time import time
from collections import deque

logger = logging.getLogger("pair_manager")

class PairStateManager:
    def __init__(self, available_pairs, state_manager, end_task_camera_map):
        self.available_pairs = available_pairs
        self.state_manager = state_manager
        self.end_task_camera_map = end_task_camera_map
        self.start_queues = [deque(p["starts"]) for p in available_pairs]
        self.end_queues = [deque(p["ends"]) for p in available_pairs]
        self.pair_states = {}
        self.sent_pairs = {}  # (cid, sidx, eidx) -> timestamp
        self.initialize_pair_states()

    def initialize_pair_states(self):
        try:
            for camera_id, pairs in enumerate(self.available_pairs):
                for start_idx in pairs["starts"]:
                    for end_idx in pairs["ends"]:
                        self.pair_states[(camera_id, start_idx, end_idx)] = {
                            "timer": None
                        }
            logger.info("Pair states initialized with available pairs")
        except Exception as e:
            logger.error(f"Error initializing pair states: {e}")
            raise

    def mark_post_sent(self, camera_id: int, start_idx: str, end_idx: str, sent: bool, success: bool = True, lock=None):
        try:
            pair_key = (camera_id, start_idx, end_idx)
            with lock:
                if sent and success:
                    self.sent_pairs[pair_key] = time.time()
                    logger.info(f"Marked pair {pair_key} as sent, added to sent_pairs")
                elif not sent and pair_key in self.sent_pairs:
                    del self.sent_pairs[pair_key]
                    logger.info(f"Removed pair {pair_key} from sent_pairs")
        except Exception as e:
            logger.error(f"Error marking post_sent: {e}")
            raise