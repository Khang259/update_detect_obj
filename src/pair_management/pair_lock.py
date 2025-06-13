import logging

logger = logging.getLogger("pair_manager")

class PairLockManager:
    def __init__(self, pair_state_manager, lock):
        self.pair_state_manager = pair_state_manager
        self.lock = lock
        self.locked_pairs = set()
        self.active_start_paths = {}
        self.active_end_paths = {}
        self.retry_counts = {}

    def lock_pair(self, start_idx, end_idx, camera_id):
        with self.lock:
            pair_key = (camera_id, start_idx, end_idx)
            self.active_start_paths[start_idx] = (camera_id, end_idx)
            self.active_end_paths[end_idx] = (camera_id, start_idx)
            self.locked_pairs.add(pair_key)
            logger.info(f"Locked pair {pair_key}, active_start_paths={self.active_start_paths}, active_end_paths={self.active_end_paths}")

    def release_pair(self, start_idx, end_idx, camera_id, due_to_invalid_state=False, due_to_timeout=False):
        with self.lock:
            pair_key = (camera_id, start_idx, end_idx)
            released = False
            if start_idx in self.active_start_paths and self.active_start_paths[start_idx] == (camera_id, end_idx):
                logger.info(f"Releasing start path {start_idx} {'due to invalid state' if due_to_invalid_state else 'due to timeout' if due_to_timeout else ''}")
                del self.active_start_paths[start_idx]
                released = True
            if end_idx in self.active_end_paths and self.active_end_paths[end_idx] == (camera_id, start_idx):
                logger.info(f"Releasing end path {end_idx} {'due to invalid state' if due_to_invalid_state else 'due to timeout' if due_to_timeout else ''}")
                del self.active_end_paths[end_idx]
                released = True
            if released:
                self.locked_pairs.discard(pair_key)
                if due_to_invalid_state or due_to_timeout:
                    logger.info(f"Released pair {pair_key} {'due to invalid state' if due_to_invalid_state else 'due to timeout'}")