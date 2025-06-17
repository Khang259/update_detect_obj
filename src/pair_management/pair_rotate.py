import logging
from collections import deque

logger = logging.getLogger("pair_manager")

class PairRotateManager:
    def __init__(self, pair_state_manager, lock):
        self.pair_state_manager = pair_state_manager
        self.lock = lock
        logger.debug("PairRotateManager initialized")

    def rotate_queues(self, camera_id: int):
        try:
            with self.lock:
                if camera_id >= len(self.pair_state_manager.start_queues) or camera_id >= len(self.pair_state_manager.end_queues):
                    logger.error(f"Invalid camera_id {camera_id}, out of range")
                    return

                logger.debug(f"Before repopulate: available_pairs[{camera_id}]={self.pair_state_manager.available_pairs[camera_id]}")
                # Làm mới queues từ available_pairs
                self.pair_state_manager.start_queues[camera_id] = deque(self.pair_state_manager.available_pairs[camera_id]["starts"])
                self.pair_state_manager.end_queues[camera_id] = deque(self.pair_state_manager.available_pairs[camera_id]["ends"])
                logger.debug(f"Repopulated queues for camera {camera_id}: "
                             f"start_queue={list(self.pair_state_manager.start_queues[camera_id])}, "
                             f"end_queue={list(self.pair_state_manager.end_queues[camera_id])}")

                # Xóa pair_states cũ cho camera_id
                old_pairs = [(k, v) for k, v in self.pair_state_manager.pair_states.items() if k[0] == camera_id]
                for (cid, sidx, eidx), _ in old_pairs:
                    del self.pair_state_manager.pair_states[(cid, sidx, eidx)]
                # Tạo lại pair_states mới
                for start_idx in self.pair_state_manager.available_pairs[camera_id]["starts"]:
                    for end_idx in self.pair_state_manager.available_pairs[camera_id]["ends"]:
                        self.pair_state_manager.pair_states[(camera_id, start_idx, end_idx)] = {
                            "timer": None
                        }
                logger.info(
                    f"Rotated queues for camera {camera_id}, new pairs created, "
                    f"start_queue={list(self.pair_state_manager.start_queues[camera_id])}, "
                    f"end_queue={list(self.pair_state_manager.end_queues[camera_id])}, "
                    f"sent_pairs={self.pair_state_manager.sent_pairs}"
                )
        except Exception as e:
            logger.error(f"Error rotating queues: {e}")
            raise