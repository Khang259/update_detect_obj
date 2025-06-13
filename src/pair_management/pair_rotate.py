import logging

logger = logging.getLogger("pair_manager")

class PairRotateManager:
    def __init__(self, pair_state_manager, lock):
        self.pair_state_manager = pair_state_manager
        self.lock = lock

    def rotate_queues(self, camera_id: int):
        try:
            with self.lock:
                if camera_id in self.pair_state_manager.start_queues and camera_id in self.pair_state_manager.end_queues:
                    self.pair_state_manager.start_queues[camera_id].rotate(-1)
                    self.pair_state_manager.end_queues[camera_id].rotate(-1)
                    old_pairs = [(k, v) for k, v in self.pair_state_manager.pair_states.items() if k[0] == camera_id]
                    for (cid, sidx, eidx), _ in old_pairs:
                        del self.pair_state_manager.pair_states[(cid, sidx, eidx)]
                        self.pair_state_manager.locked_pairs.discard((cid, sidx, eidx))
                        if sidx in self.pair_state_manager.active_start_paths and self.pair_state_manager.active_start_paths[sidx] == (cid, eidx):
                            del self.pair_state_manager.active_start_paths[sidx]
                        if eidx in self.pair_state_manager.active_end_paths and self.pair_state_manager.active_end_paths[eidx] == (cid, sidx):
                            del self.pair_state_manager.active_end_paths[eidx]
                        if (cid, sidx, eidx) in self.pair_state_manager.retry_counts:
                            del self.pair_state_manager.retry_counts[(cid, sidx, eidx)]
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