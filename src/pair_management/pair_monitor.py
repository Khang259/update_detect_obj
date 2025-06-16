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
                                f"active_end_paths={self.pair_lock_manager.active_end_paths}"
                            )
                            self._last_status_log = time.time()
                            logger.handlers[0].flush()

                        start_queue = self.pair_state_manager.start_queues[camera_id]
                        end_queue = self.pair_state_manager.end_queues[camera_id]
                        logger.debug(f"Camera {camera_id}: start_queue={list(start_queue)}, end_queue={list(end_queue)}")
                        available_pairs = []

                        # Chọn phần tử đầu tiên hợp lệ từ start_queue và end_queue
                        selected_start_idx = None
                        selected_end_idx = None

                        # Kiểm tra end_queue trước
                        if end_queue:
                            end_idx = end_queue[0]
                            if end_idx not in self.pair_lock_manager.active_end_paths:
                                end_camera_id = self.pair_state_manager.end_task_camera_map.get(end_idx, camera_id)
                                end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                                logger.debug(f"Checked end path {end_idx} (camera {end_camera_id}): end_state={end_state}")
                                if end_state is False:
                                    selected_end_idx = end_idx

                        # Kiểm tra start_queue nếu đã chọn được end_idx
                        if selected_end_idx is not None and start_queue:
                            start_idx = start_queue[0]
                            if start_idx not in self.pair_lock_manager.active_start_paths:
                                start_state = self.pair_state_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
                                logger.debug(f"Checked start path {start_idx} (camera {camera_id}): start_state={start_state}")
                                if start_state is True and not any(
                                    (cid, sidx, _) in self.pair_state_manager.sent_pairs
                                    for cid, sidx, _ in self.pair_state_manager.pair_states
                                    if sidx == start_idx
                                ):
                                    selected_start_idx = start_idx

                        # Tạo cặp nếu cả hai hợp lệ
                        if selected_start_idx is not None and selected_end_idx is not None:
                            pair_key = (camera_id, selected_start_idx, selected_end_idx)
                            if (
                                pair_key in self.pair_state_manager.pair_states and
                                pair_key not in self.pair_lock_manager.locked_pairs and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                available_pairs.append(pair_key)
                                logger.debug(f"Added pair {pair_key} to available_pairs")

                        logger.debug(f"Available pairs for camera {camera_id}: {available_pairs}")
                        for pair_key in list(self.pair_state_manager.pair_states.keys()):
                            cid, sidx, eidx = pair_key
                            if cid != camera_id:
                                logger.debug(f"Skipping pair {pair_key} (camera {cid} != {camera_id})")
                                continue
                            if sidx not in start_queue or eidx not in end_queue:
                                logger.debug(f"Skipping pair {pair_key}: sidx={sidx} or eidx={eidx} not in queues")
                                continue  # Bỏ qua cặp nếu sidx hoặc eidx không còn trong queues
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
                                # Loại bỏ start_idx và end_idx nếu là phần tử đầu tiên
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.popleft()
                                    logger.debug(f"Removed {sidx} from start_queue: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.popleft()
                                    logger.debug(f"Removed {eidx} from end_queue: {list(end_queue)}")

                            # Release locks for sent pairs with invalid states
                            elif (
                                pair_key in self.pair_state_manager.sent_pairs and
                                (start_state is False or end_state is True)
                            ):
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                if pair_key in self.pair_state_manager.sent_pairs:
                                    logger.info(f"Removing pair {pair_key} from sent_pairs due to invalid state")
                                    del self.pair_state_manager.sent_pairs[pair_key]
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.popleft()
                                    logger.debug(f"Removed {sidx} from start_queue due to invalid state: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.popleft()
                                    logger.debug(f"Removed {eidx} from end_queue due to invalid state: {list(end_queue)}")

                            # Timeout for sent pairs
                            elif (
                                pair_key in self.pair_state_manager.sent_pairs and
                                time.time() - self.pair_state_manager.sent_pairs[pair_key] >= 300
                            ):
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_timeout=True)
                                logger.info(f"Removing pair {pair_key} from sent_pairs due to timeout")
                                del self.pair_state_manager.sent_pairs[pair_key]
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.popleft()
                                    logger.debug(f"Removed {sidx} from start_queue due to timeout: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.popleft()
                                    logger.debug(f"Removed {eidx} from end_queue due to timeout: {list(end_queue)}")

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
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.popleft()
                                    logger.debug(f"Removed {sidx} from start_queue due to invalid state: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.popleft()
                                    logger.debug(f"Removed {eidx} from end_queue due to invalid state: {list(end_queue)}")

                            # Reset stuck timers
                            elif (
                                info["timer"] and
                                time.time() - info["timer"] >= 300 and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                logger.warning(f"Resetting stuck timer for pair ({cid}, {sidx}, {eidx}) after 300s")
                                self.pair_lock_manager.release_pair(sidx, eidx, cid)
                                info["timer"] = None
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.popleft()
                                    logger.debug(f"Removed {sidx} from start_queue due to stuck timer: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.popleft()
                                    logger.debug(f"Removed {eidx} from end_queue due to stuck timer: {list(end_queue)}")

                        # Làm mới queues nếu cả hai rỗng
                        if not start_queue and not end_queue:
                            logger.info(f"Both queues empty for camera {camera_id}, repopulating queues")
                            self.pair_rotate_manager.rotate_queues(camera_id)

                    logger.debug(f"Released lock for camera {camera_id}")

                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}", exc_info=True)
                logger.handlers[0].flush()
                print(f"Error in monitor_pairs: {e}\n{traceback.format_exc()}")
                time.sleep(1)