import logging
import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("pair_manager")

class PairMonitorThread(threading.Thread):
    def __init__(self, camera_ids, pair_manager, pair_state_manager, pair_rotate_manager, pair_lock_manager, pair_post_manager, queue_manager, shutdown_event):
        super().__init__()
        self.camera_ids = camera_ids
        self.pair_manager = pair_manager
        self.pair_state_manager = pair_state_manager
        self.pair_rotate_manager = pair_rotate_manager
        self.pair_lock_manager = pair_lock_manager
        self.pair_post_manager = pair_post_manager
        self.queue_manager = queue_manager
        self.shutdown_event = shutdown_event
        self.running = True
        logger.debug(f"PairMonitorThread initialized for cameras {camera_ids}")

    def run(self):
        logger.info(f"Starting PairMonitorThread for cameras {self.camera_ids}")
        thread_name = threading.current_thread().name
        last_queue_refresh = {cid: 0 for cid in self.camera_ids}
        while self.running and not self.shutdown_event.is_set():
            logger.debug(f"Thread {thread_name}: Starting iteration")
            try:
                start_time = time.time()
                for camera_id in self.camera_ids:
                    try:
                        with self.pair_manager.locks[camera_id]:
                            start_queue = self.pair_state_manager.start_queues[camera_id]
                            end_queue = self.pair_state_manager.end_queues[camera_id]
                            logger.debug(f"Camera {camera_id}: start_queue={list(start_queue)}, end_queue={list(end_queue)}")

                            valid_end_list = []
                            valid_start_list = []

                            # Kiểm tra end_queue và thêm vào QueueManager
                            if end_queue:
                                for end_idx in list(end_queue):
                                    if any(e == end_idx for _, _, e in self.pair_state_manager.sent_pairs):
                                        continue
                                    if end_idx not in self.pair_lock_manager.active_end_paths:
                                        end_camera_id = self.pair_state_manager.end_task_camera_map.get(end_idx, camera_id)
                                        end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                                        logger.debug(f"End path {end_idx} (camera {end_camera_id}): end_state={end_state}")
                                        if end_state is False:
                                            valid_end_list.append(end_idx)
                                            self.queue_manager.add_end_idx(camera_id, end_idx)

                            # Kiểm tra start_queue
                            if start_queue:
                                for start_idx in list(start_queue):
                                    if start_idx not in self.pair_lock_manager.active_start_paths:
                                        start_state = self.pair_state_manager.state_manager.get_state(camera_id, f"starts_{start_idx}")
                                        logger.debug(f"Start path {start_idx}: start_state={start_state}")
                                        if start_state is True and not any(
                                            (cid, sidx, _) in self.pair_state_manager.sent_pairs
                                            for cid, sidx, _ in self.pair_state_manager.pair_states
                                            if sidx == start_idx
                                        ):
                                            valid_start_list.append(start_idx)

                            logger.debug(f"Camera {camera_id}: valid_end_list={valid_end_list}, valid_start_list={valid_start_list}")

                            # Ghép cặp từ queue
                            available_pairs = []
                            available_pairs_config = self.pair_state_manager.available_pairs[camera_id]
                            while True:
                                end_item = self.queue_manager.get_end_idx()
                                if not end_item:
                                    break
                                cid, end_idx = end_item
                                if cid != camera_id:
                                    continue
                                for start_idx in valid_start_list:
                                    if (
                                        start_idx in available_pairs_config["starts"] and
                                        end_idx in available_pairs_config["ends"]
                                    ):
                                        pair_key = (camera_id, start_idx, end_idx)
                                        with self.pair_lock_manager.lock:
                                            if (
                                                pair_key in self.pair_state_manager.pair_states and
                                                pair_key not in self.pair_lock_manager.locked_pairs and
                                                pair_key not in self.pair_state_manager.sent_pairs
                                            ):
                                                if self.pair_lock_manager.lock_pair(start_idx, end_idx, camera_id):
                                                    available_pairs.append(pair_key)
                                                    logger.debug(f"Locked pair {pair_key}")
                                                    break
                                if available_pairs:
                                    break

                            # Xử lý cặp
                            for pair_key in list(self.pair_state_manager.pair_states.keys()):
                                cid, sidx, eidx = pair_key
                                if cid != camera_id:
                                    continue
                                if sidx not in start_queue or eidx not in end_queue:
                                    continue
                                info = self.pair_state_manager.pair_states[pair_key]
                                start_state = self.pair_state_manager.state_manager.get_state(cid, f"starts_{sidx}")
                                end_camera_id = self.pair_state_manager.end_task_camera_map.get(eidx, cid)
                                end_state = self.pair_state_manager.state_manager.get_state(end_camera_id, f"ends_{eidx}")
                                elapsed = time.time() - info["timer"] if info["timer"] else 0
                                logger.debug(
                                    f"Checking pair ({cid}, {sidx}, {eidx}): start={start_state}, end={end_state}, "
                                    f"timer={elapsed:.2f}s, in_sent_pairs={pair_key in self.pair_state_manager.sent_pairs}"
                                )

                                # Start timer
                                if pair_key in available_pairs and info["timer"] is None and pair_key not in self.pair_state_manager.sent_pairs:
                                    if start_state is True and end_state is False:
                                        info["timer"] = time.time()
                                        logger.info(f"Timer started for camera {cid}, pair ({sidx}, {eidx})")
                                    else:
                                        self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)

                                # Trigger POST
                                elif (
                                    start_state is True and
                                    end_state is False and
                                    info["timer"] and
                                    time.time() - info["timer"] >= 10 and
                                    pair_key not in self.pair_state_manager.sent_pairs
                                ):
                                    with self.pair_lock_manager.lock:
                                        if any(e == eidx for _, _, e in self.pair_state_manager.sent_pairs):
                                            self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                            continue
                                        self.pair_post_manager.trigger_post(cid, sidx, eidx)
                                        self.pair_state_manager.sent_pairs[pair_key] = time.time()
                                        info["timer"] = None
                                        logger.info(f"Triggered POST for camera {cid}, pair ({sidx}, {eidx})")
                                        if start_queue and sidx == start_queue[0]:
                                            start_queue.rotate(-1)
                                        if end_queue and eidx == end_queue[0]:
                                            end_queue.rotate(-1)

                                # Release sent pairs
                                elif pair_key in self.pair_state_manager.sent_pairs:
                                    sent_time = self.pair_state_manager.sent_pairs[pair_key]
                                    if start_state is False:
                                        self.pair_lock_manager.release_pair(sidx, eidx, cid, release_start_only=True)
                                    if end_state is True or time.time() - sent_time >= 300:
                                        self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=end_state is True)
                                        del self.pair_state_manager.sent_pairs[pair_key]
                                        if start_queue and sidx == start_queue[0]:
                                            start_queue.rotate(-1)
                                        if end_queue and eidx == end_queue[0]:
                                            end_queue.rotate(-1)

                                # Reset invalid states
                                elif (
                                    (start_state is False or end_state is True) and
                                    pair_key not in self.pair_state_manager.sent_pairs
                                ):
                                    if info["timer"]:
                                        logger.info(f"Resetting timer for pair ({cid}, {sidx}, {eidx})")
                                    self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)
                                    info["timer"] = None
                                    if start_queue and sidx == start_queue[0]:
                                        start_queue.rotate(-1)
                                    if end_queue and eidx == end_queue[0]:
                                        end_queue.rotate(-1)

                                # Reset stuck timers
                                elif (
                                    info["timer"] and
                                    time.time() - info["timer"] >= 300 and
                                    pair_key not in self.pair_state_manager.sent_pairs
                                ):
                                    logger.warning(f"Resetting stuck timer for pair ({cid}, {sidx}, {eidx})")
                                    self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_timeout=True)
                                    info["timer"] = None
                                    if start_queue and sidx == start_queue[0]:
                                        start_queue.rotate(-1)
                                    if end_queue and eidx == end_queue[0]:
                                        end_queue.rotate(-1)

                            # Làm mới queue
                            current_time = time.time()
                            if not start_queue or not end_queue or current_time - last_queue_refresh[camera_id] >= 60:
                                logger.info(f"Repopulating queues for camera {camera_id}")
                                saved_timers = {(cid, sidx, eidx): info["timer"] for (cid, sidx, eidx), info in self.pair_state_manager.pair_states.items() if cid == camera_id}
                                self.pair_rotate_manager.rotate_queues(camera_id)
                                for (cid, sidx, eidx), timer in saved_timers.items():
                                    if (cid, sidx, eidx) in self.pair_state_manager.pair_states and timer is not None:
                                        self.pair_state_manager.pair_states[(cid, sidx, eidx)]["timer"] = timer
                                last_queue_refresh[camera_id] = current_time
                                for (cid, sidx, eidx) in list(self.pair_state_manager.pair_states.keys()):
                                    if cid == camera_id and (cid, sidx, eidx) not in self.pair_state_manager.sent_pairs:
                                        self.pair_lock_manager.release_pair(sidx, eidx, cid, due_to_invalid_state=True)

                    except Exception as e:
                        logger.error(f"Error processing camera {camera_id}: {e}", exc_info=True)

                logger.debug(f"Iteration took {time.time() - start_time:.2f}s")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in PairMonitorThread: {e}", exc_info=True)
                time.sleep(1)

class PairMonitor:
    def __init__(self, pair_manager, pair_state_manager, pair_rotate_manager, pair_lock_manager, pair_post_manager, queue_manager):
        self.pair_manager = pair_manager
        self.pair_state_manager = pair_state_manager
        self.pair_rotate_manager = pair_rotate_manager
        self.pair_lock_manager = pair_lock_manager
        self.pair_post_manager = pair_post_manager
        self.queue_manager = queue_manager
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)  # 20 threads for 200 cameras (~10 cameras/thread)
        self.threads = []
        logger.debug("PairMonitor initialized")

    def start_monitoring(self):
        num_cameras = len(self.pair_state_manager.available_pairs)
        cameras_per_thread = max(1, num_cameras // 20)
        for i in range(0, num_cameras, cameras_per_thread):
            camera_ids = list(range(i, min(i + cameras_per_thread, num_cameras)))
            thread = PairMonitorThread(
                camera_ids, self.pair_manager, self.pair_state_manager, self.pair_rotate_manager,
                self.pair_lock_manager, self.pair_post_manager, self.queue_manager, self.shutdown_event
            )
            self.threads.append(thread)
            self.executor.submit(thread.run)
            logger.info(f"Started PairMonitorThread for cameras {camera_ids}")
        return self.threads

    def stop_monitoring(self):
        self.shutdown_event.set()
        for thread in self.threads:
            thread.running = False
        self.executor.shutdown(wait=True)
        logger.info("PairMonitor stopped")