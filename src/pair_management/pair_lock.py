import logging
import threading

logger = logging.getLogger("pair_manager")

class PairLockManager:
    def __init__(self, pair_state_manager, lock):
        self.pair_state_manager = pair_state_manager
        self.lock = lock
        self.locked_pairs = set()
        self.active_start_paths = {}
        self.active_end_paths = {}
        self.retry_counts = {}
        logger.debug("PairLockManager initialized")

    def lock_pair(self, start_idx, end_idx, camera_id):
        """Khóa cặp, kiểm tra active paths để tránh race condition"""
        logger.debug(f"Attempting to lock pair ({camera_id}, {start_idx}, {end_idx})")
        try:
            with self.lock:
                pair_key = (camera_id, start_idx, end_idx)
                if pair_key in self.locked_pairs:
                    logger.warning(f"Pair {pair_key} already locked")
                    return False
                if start_idx in self.active_start_paths or end_idx in self.active_end_paths:
                    logger.debug(f"Start {start_idx} or end {end_idx} active, skipping")
                    return False
                self.locked_pairs.add(pair_key)
                self.active_start_paths[start_idx] = (camera_id, end_idx)
                self.active_end_paths[end_idx] = (camera_id, start_idx)
                logger.debug(f"Locked pair {pair_key}, active_start_paths={self.active_start_paths}, active_end_paths={self.active_end_paths}")
                return True
        except Exception as e:
            logger.error(f"Error locking pair ({camera_id}, {start_idx}, {end_idx}): {e}", exc_info=True)
            return False

    def release_pair(self, start_idx, end_idx, camera_id, due_to_invalid_state=False, due_to_timeout=False, release_start_only=False):
        """Giải phóng khóa"""
        logger.debug(f"Releasing pair ({camera_id}, {start_idx}, {end_idx}), release_start_only={release_start_only}")
        try:
            with self.lock:
                pair_key = (camera_id, start_idx, end_idx)
                self.locked_pairs.discard(pair_key)
                if start_idx in self.active_start_paths:
                    del self.active_start_paths[start_idx]
                if not release_start_only and end_idx in self.active_end_paths:
                    del self.active_end_paths[end_idx]
                if pair_key in self.retry_counts:
                    del self.retry_counts[pair_key]
                logger.debug(f"Released pair {pair_key}, active_start_paths={self.active_start_paths}, active_end_paths={self.active_end_paths}")
        except Exception as e:
            logger.error(f"Error releasing pair ({camera_id}, {start_idx}, {end_idx}): {e}", exc_info=True)