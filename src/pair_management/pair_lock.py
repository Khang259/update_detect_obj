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
        logger.debug(f"Locking pair ({camera_id}, {start_idx}, {end_idx})")
        with self.lock:
            pair_key = (camera_id, start_idx, end_idx)
            self.locked_pairs.add(pair_key)
            # Cập nhật active paths
            logger.debug(f"Locked pair {pair_key}")

    def release_pair(self, start_idx, end_idx, camera_id, due_to_invalid_state=False, due_to_timeout=False):
        logger.debug(f"Releasing pair ({camera_id}, {start_idx}, {end_idx})")
        with self.lock:
            pair_key = (camera_id, start_idx, end_idx)
            self.locked_pairs.discard(pair_key)
            # Cập nhật active paths
            logger.debug(f"Released pair {pair_key}")