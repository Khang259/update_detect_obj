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
        self.no_pairs_count = {}  # Đếm chu kỳ không tạo cặp
        logger.debug("PairMonitor initialized")

    def monitor_pairs(self):
        logger.info("Starting pair monitoring")
        thread_name = threading.current_thread().name
        while self.running:
            print(f"Monitoring pairs... (Thread: {thread_name}, Running: {self.running})")
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
                        start_queue = self.pair_state_manager.start_queues[camera_id]
                        end_queue = self.pair_state_manager.end_queues[camera_id]
                        logger.debug(f"Camera {camera_id}: start_queue={list(start_queue)}, end_queue={list(end_queue)}")
                        available_pairs = []

                        # Chọn phần tử đầu tiên hợp lệ từ start_queue và end_queue
                        selected_start_idx = None
                        selected_end_idx = None

                        # Kiểm tra end_queue
                        if end_queue:
                            max_rotations = len(end_queue)
                            rotations = 0
                            while rotations < max_rotations:
                                end_idx = end_queue[0]
                                if any(e == end_idx for _, _, e in self.pair_state_manager.sent_pairs):
                                    end_queue.rotate(-1)
                                    logger.debug(f"Rotated end_queue due to end_idx {end_idx} in sent_pairs: {list(end_queue)}")
                                    rotations += 1
                                    continue
                                if end_idx not in self.pair_lock_manager.active_end_paths:
                                    end_camera_id = self.pair_state_manager.end_task_camera_map.get(end_idx, camera_id)
                                    end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                                    logger.debug(f"Checked end path {end_idx} (camera {end_camera_id}): end_state={end_state}")
                                    if end_state is False:
                                        selected_end_idx = end_idx
                                        break
                                end_queue.rotate(-1)
                                logger.debug(f"Rotated end_queue due to invalid end_idx or state: {list(end_queue)}")
                                rotations += 1
                            logger.debug(f"Selected end_idx: {selected_end_idx}, rotations: {rotations}")

                        # Kiểm tra start_queue nếu đã chọn được end_idx
                        if selected_end_idx is not None and start_queue:
                            max_rotations = len(start_queue)
                            rotations = 0
                            while rotations < max_rotations:
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
                                        break
                                start_queue.rotate(-1)
                                logger.debug(f"Rotated start_queue due to invalid start_idx or state: {list(start_queue)}")
                                rotations += 1
                            logger.debug(f"Selected start_idx: {selected_start_idx}, rotations: {rotations}")

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
                            else:
                                logger.debug(f"Pair {pair_key} not added: in_pair_states={pair_key in self.pair_state_manager.pair_states}, "
                                             f"in_locked_pairs={pair_key in self.pair_lock_manager.locked_pairs}, "
                                             f"in_sent_pairs={pair_key in self.pair_state_manager.sent_pairs}")

                        logger.debug(f"Available pairs for camera {camera_id}: {available_pairs}")
                        for pair_key in list(self.pair_state_manager.pair_states.keys()):
                            cid, sidx, eidx = pair_key
                            if cid != camera_id:
                                logger.debug(f"Skipping pair {pair_key} (camera {cid} != {camera_id})")
                                continue
                            if sidx not in start_queue or eidx not in end_queue:
                                logger.debug(f"Skipping pair {pair_key}: sidx={sidx} or eidx={eidx} not in queues")
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
                                self.pair_state_manager.sent_pairs[pair_key] = time.time()
                                info["timer"] = None
                                logger.info(f"Triggered delay_post_request for camera {cid}, pair ({sidx}, {eidx})")
                                logger.debug(f"State after POST: start_state={start_state}, end_state={end_state}, "
                                             f"sent_pairs={self.pair_state_manager.sent_pairs}")
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.rotate(-1)
                                    logger.debug(f"Rotated start_queue: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.rotate(-1)
                                    logger.debug(f"Rotated end_queue: {list(end_queue)}")

                            # Release locks for sent pairs based on states or timeout
                            elif pair_key in self.pair_state_manager.sent_pairs:
                                sent_time = self.pair_state_manager.sent_pairs[pair_key]
                                if start_state is False:
                                    self.pair_lock_manager.release_pair(sidx, eidx, cid, release_start_only=True)
                                    logger.debug(f"Released start lock for {sidx} due to start_state=False")
                                if end_state is True or time.time() - sent_time >= 300:
                                    self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=end_state is True)
                                    logger.info(f"Removing pair {pair_key} from sent_pairs due to {'end_state=True' if end_state is True else 'timeout'}")
                                    del self.pair_state_manager.sent_pairs[pair_key]
                                    if start_queue and sidx == start_queue[0]:
                                        start_queue.rotate(-1)
                                        logger.debug(f"Rotated start_queue due to {'end_state=True' if end_state is True else 'timeout'}: {list(start_queue)}")
                                    if end_queue and eidx == end_queue[0]:
                                        end_queue.rotate(-1)
                                        logger.debug(f"Rotated end_queue due to {'end_state=True' if end_state is True else 'timeout'}: {list(end_queue)}")

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
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                info["timer"] = None
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.rotate(-1)
                                    logger.debug(f"Rotated start_queue due to invalid state: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.rotate(-1)
                                    logger.debug(f"Rotated end_queue due to invalid state: {list(end_queue)}")

                            # Reset stuck timers
                            elif (
                                info["timer"] and
                                time.time() - info["timer"] >= 300 and
                                pair_key not in self.pair_state_manager.sent_pairs
                            ):
                                logger.warning(f"Resetting stuck timer for pair ({cid}, {sidx}, {eidx}) after 300s")
                                self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_timeout=True)
                                info["timer"] = None
                                if start_queue and sidx == start_queue[0]:
                                    start_queue.rotate(-1)
                                    logger.debug(f"Rotated start_queue due to stuck timer: {list(start_queue)}")
                                if end_queue and eidx == end_queue[0]:
                                    end_queue.rotate(-1)
                                    logger.debug(f"Rotated end_queue due to stuck timer: {list(end_queue)}")

                        # Làm mới queues nếu queues rỗng hoặc sau 10 chu kỳ không tạo cặp
                        self.no_pairs_count[camera_id] = self.no_pairs_count.get(camera_id, 0) + (1 if not available_pairs else 0)
                        if not start_queue or not end_queue or self.no_pairs_count[camera_id] >= 10:
                            logger.info(f"Repopulating queues for camera {camera_id}: empty_queues={not start_queue or not end_queue}, "
                                        f"no_pairs_count={self.no_pairs_count[camera_id]}")
                            saved_timers = {(cid, sidx, eidx): info["timer"] for (cid, sidx, eidx), info in self.pair_state_manager.pair_states.items() if cid == camera_id}
                            self.pair_rotate_manager.rotate_queues(camera_id)
                            for (cid, sidx, eidx), timer in saved_timers.items():
                                if (cid, sidx, eidx) in self.pair_state_manager.pair_states and timer is not None:
                                    self.pair_state_manager.pair_states[(cid, sidx, eidx)]["timer"] = timer
                                    logger.debug(f"Restored timer for pair ({cid}, {sidx}, {eidx}): {timer}")
                            self.no_pairs_count[camera_id] = 0
                            for (cid, sidx, eidx) in list(self.pair_state_manager.pair_states.keys()):
                                if cid == camera_id and (cid, sidx, eidx) not in self.pair_state_manager.sent_pairs:
                                    self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                    logger.debug(f"Released locks for pair ({cid}, {sidx}, {eidx}) after queue rotation")

                    logger.debug(f"Released lock for camera {camera_id}")

                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}", exc_info=True)
                logger.handlers[0].flush()
                print(f"Error in monitor_pairs: {e}\n{traceback.format_exc()}")
                time.sleep(1)