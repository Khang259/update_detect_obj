import logging
import time
import threading
import traceback
from collections import deque

logger = logging.getLogger("pair_manager")

class PairMonitor:
    def __init__(self, pair_manager, pair_state_manager, pair_rotate_manager, pair_lock_manager, pair_post_manager):
        self.pair_manager = pair_manager
        self.pair_state_manager = pair_state_manager
        self.pair_rotate_manager = pair_rotate_manager
        self.pair_lock_manager = pair_lock_manager
        self.pair_post_manager = pair_post_manager
        self.running = True
        self._last_status_log = 0
        logger.debug("PairMonitor initialized")

    def monitor_pairs(self):
        logger.info("Starting pair monitoring")
        thread_name = threading.current_thread().name
        while self.running:
            print(f"Monitoring pairs... (Thread: {thread_name}, Running: {self.running})")
            logger.debug(f"Thread {thread_name}: Starting new monitor_pairs iteration, running={self.running}")
            try:
                num_cameras = len(self.pair_state_manager.available_pairs)
                logger.debug(f"Number of cameras: {num_cameras}")
                if num_cameras == 0:
                    logger.warning("No available pairs, sleeping...")
                    time.sleep(0.1)
                    continue

                for camera_id in range(num_cameras):
                    logger.debug(f"Processing camera {camera_id}")
                    logger.debug(f"Attempting to acquire lock for camera {camera_id}")
                    with self.pair_manager.locks[camera_id]:
                        logger.debug(f"Acquired lock for camera {camera_id}")
                        if time.time() - self._last_status_log >= 60:
                            logger.info(
                                f"Current pair_states: {len(self.pair_state_manager.pair_states)} pairs, "
                                f"sent_pairs: {self.pair_state_manager.sent_pairs}, "
                                f"active_start_paths: {self.pair_lock_manager.active_start_paths}, "
                                f"active_end_paths: {self.pair_lock_manager.active_end_paths}"
                            )
                            self._last_status_log = time.time()
                            logger.handlers[0].flush()

                        end_queue = list(self.pair_state_manager.end_queues[camera_id])
                        start_queue = list(self.pair_state_manager.start_queues[camera_id])
                        logger.debug(f"Camera {camera_id}: start_queue={start_queue}, end_queue={end_queue}")
                        available_pairs = []
                        used_starts = set()
                        used_ends = set()

                        # Chỉ lấy phần tử đầu tiên trong end_queue có end_state=False
                        selected_end_idx = None
                        for end_idx in end_queue:
                            if end_idx in used_ends or end_idx in self.pair_lock_manager.active_end_paths:
                                logger.debug(f"End path {end_idx} is used or active, skipping")
                                continue
                            end_camera_id = self.pair_state_manager.end_task_camera_map.get(end_idx, camera_id)
                            end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                            logger.debug(f"Checked end path {end_idx} (camera {end_camera_id}): end_state={end_state}")
                            if end_state is False:
                                selected_end_idx = end_idx
                                break  # Lấy end_idx đầu tiên hợp lệ

                        if selected_end_idx is not None:
                            # Tìm start_idx hợp lệ để ghép với selected_end_idx
                            for start_idx in start_queue:
                                if start_idx in used_starts or start_idx in self.pair_lock_manager.active_start_paths:
                                    logger.debug(f"Start path {start_idx} is used or active, skipping")
                                    continue
                                start_state = self.pair_state_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
                                logger.debug(f"Checked start path {start_idx} (camera {camera_id}): start_state={start_state}")
                                pair_key = (camera_id, start_idx, selected_end_idx)
                                # Kiểm tra start_idx không được tái sử dụng nếu đang trong sent_pairs
                                if any((cid, sidx, _) in self.pair_state_manager.sent_pairs for cid, sidx, _ in self.pair_state_manager.pair_states if sidx == start_idx):
                                    logger.debug(f"Start path {start_idx} in sent_pairs, skipping")
                                    continue
                                if (
                                    start_state is True and
                                    pair_key in self.pair_state_manager.pair_states and
                                    pair_key not in self.pair_lock_manager.locked_pairs and
                                    pair_key not in self.pair_state_manager.sent_pairs
                                ):
                                    available_pairs.append(pair_key)
                                    used_starts.add(start_idx)
                                    used_ends.add(selected_end_idx)
                                    logger.debug(f"Added pair {pair_key} to available_pairs")
                                    break  # Chỉ ghép một start_idx với selected_end_idx

                        logger.debug(f"Available pairs for camera {camera_id}: {available_pairs}")
                        for pair_key in list(self.pair_state_manager.pair_states.keys()):
                            cid, sidx, eidx = pair_key
                            if cid != camera_id:
                                logger.debug(f"Skipping pair {pair_key} (camera {cid} != {camera_id})")
                                continue
                            info = self.pair_state_manager.pair_states[pair_key]
                            logger.debug(f"Getting start state for pair {pair_key}")
                            start_state = self.pair_state_manager.state_manager.get_state(cid, f"starts_{sidx}")
                            end_camera_id = self.pair_state_manager.end_task_camera_map.get(eidx, cid)
                            logger.debug(f"Getting end state for pair {pair_key}")
                            end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{eidx}")
                            elapsed = time.time() - info["timer"] if info["timer"] else 0
                            logger.debug(
                                f"Checking pair ({cid}, {sidx}, {eidx}): "
                                f"start={start_state}, end={end_state}, end_camera={end_camera_id}, "
                                f"timer={elapsed:.2f}s, in_sent_pairs={pair_key in self.pair_state_manager.sent_pairs}, "
                                f"active_end_paths={self.pair_lock_manager.active_end_paths}, "
                                f"active_start_paths={self.pair_lock_manager.active_start_paths}, "
                                f"retry_counts={self.pair_lock_manager.retry_counts}"
                            )
                            logger.handlers[0].flush()

                            # Start timer
                            if pair_key in available_pairs and info["timer"] is None and pair_key not in self.pair_state_manager.sent_pairs:
                                start_state = self.pair_state_manager.state_manager.get_state(cid, f"starts_{sidx}")
                                end_camera_id = self.pair_state_manager.end_task_camera_map.get(eidx, cid)
                                end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{eidx}")
                                logger.debug(f"Preparing to lock pair {pair_key}: start_state={start_state}, end_state={end_state}")
                                if start_state is True and end_state is False:
                                    self.pair_lock_manager.lock_pair(sidx, eidx, cid)
                                    info["timer"] = time.time()
                                    logger.info(
                                        f"Timer started for camera {cid}, pair ({sidx}, {eidx}), "
                                        f"active_end_paths={self.pair_lock_manager.active_end_paths}, "
                                        f"active_start_paths={self.pair_lock_manager.active_start_paths}"
                                    )
                                else:
                                    logger.debug(f"Skipping timer start for pair {pair_key}: invalid state (start={start_state}, end={end_state})")

                            # Trigger POST
                            elif (
                                start_state is True and
                                end_state is False and
                                info["timer"] and
                                time.time() - info["timer"] >= 10 and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                self.pair_post_manager.trigger_post(cid, sidx, eidx)
                                info["timer"] = None
                                logger.info(f"Triggered delay_post_request for camera {cid}, pair ({sidx}, {eidx})")

                            # Release locks for sent pairs with invalid states
                            elif (
                                pair_key in self.pair_state_manager.sent_pairs and
                                (start_state is False or end_state is True)
                            ):
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                if pair_key in self.pair_state_manager.sent_pairs:
                                    logger.info(f"Removing pair {pair_key} from sent_pairs due to invalid state")
                                    del self.pair_state_manager.sent_pairs[pair_key]

                            # Timeout for sent pairs
                            elif (
                                pair_key in self.pair_state_manager.sent_pairs and
                                time.time() - self.pair_state_manager.sent_pairs[pair_key] >= 300
                            ):
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_timeout=True)
                                logger.info(f"Removing pair {pair_key} from sent_pairs due to timeout")
                                del self.pair_state_manager.sent_pairs[pair_key]

                            # Delay reset for invalid states
                            elif (
                                (start_state is False or end_state is True) and
                                info["timer"] and
                                time.time() - info["timer"] < 10
                            ):
                                logger.debug(f"Delaying reset for pair ({cid}, {sidx}, {eidx}) due to recent timer start")

                            # Reset for invalid states (non-sent pairs)
                            elif (
                                (start_state is False or end_state is True) and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                if info["timer"]:
                                    logger.info(f"Resetting timer for pair ({cid}, {sidx}, {eidx}) due to invalid state")
                                self.pair_lock_manager.release_pair(sidx, eidx, cid)
                                info["timer"] = None

                            # Reset stuck timers
                            elif (
                                info["timer"] and
                                time.time() - info["timer"] >= 300 and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                logger.warning(f"Resetting stuck timer for pair ({cid}, {sidx}, {eidx}) after 300s")
                                self.pair_lock_manager.release_pair(sidx, eidx, cid)
                                info["timer"] = None

                        # Rotate queues
                        all_processed = all(
                            pair_key in self.pair_state_manager.sent_pairs or (
                                self.pair_state_manager.state_manager.get_state(camera_id, f"starts_{start_idx}") is False or
                                self.pair_state_manager.state_manager.get_state(
                                    self.pair_state_manager.end_task_camera_map.get(end_idx, camera_id), f"ends_{end_idx}"
                                ) is True
                            )
                            for (cid, start_idx, end_idx) in self.pair_state_manager.pair_states
                            if cid == camera_id
                        )
                        if all_processed:
                            self.pair_rotate_manager.rotate_queues(camera_id)
                            logger.info(f"Rotated queues for camera {camera_id} due to all pairs processed")
                            logger.handlers[0].flush()

                    logger.debug(f"Released lock for camera {camera_id}")

                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}", exc_info=True)
                logger.handlers[0].flush()
                print(f"Error in monitor_pairs: {e}\n{traceback.format_exc()}")
                time.sleep(1)