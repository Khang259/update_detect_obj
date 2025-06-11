import threading
import time
import logging
from collections import deque
from datetime import datetime
import os
from post_request import delay_post_request

# Logging configuration
os.makedirs("logs", exist_ok=True)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
date_str = datetime.now().strftime("%Y%m%d")
log_handler = logging.FileHandler(f"logs/log_pair_manager_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler("logs/log_error.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.DEBUG)

logger = logging.getLogger("pair_manager")
logger.setLevel(logging.DEBUG)  # Enhanced debugging
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class PairManager:
    def __init__(self, available_pairs, state_manager, api_url):
        self.available_pairs = available_pairs
        self.state_manager = state_manager
        self.api_url = api_url
        self.start_queues = [deque(p["starts"]) for p in available_pairs]
        self.end_queues = [deque(p["ends"]) for p in available_pairs]
        self.pair_states = {}
        self.sent_pairs = {}  # (cid, sidx, eidx) -> timestamp
        self.locked_pairs = set()
        self.active_start_paths = {}
        self.active_end_paths = {}
        self.retry_counts = {}
        self.lock = threading.Lock()
        self.running = True
        self.end_task_camera_map = {
            "10000164": 0, "10000170": 2, "10000171": 2, "10000140": 2,
            "10000141": 2, "10000147": 1
        }
        try:
            for camera_id, pairs in enumerate(available_pairs):
                for start_idx in pairs["starts"]:
                    for end_idx in pairs["ends"]:
                        self.pair_states[(camera_id, start_idx, end_idx)] = {
                            "timer": None
                        }
            logger.info("PairManager initialized with available pairs")
        except Exception as e:
            logger.error(f"Error initializing PairManager: {e}")
            raise

    def mark_post_sent(self, camera_id: int, start_idx: str, end_idx: str, sent: bool, success: bool = True):
        try:
            pair_key = (camera_id, start_idx, end_idx)
            with self.lock:
                if sent and success:
                    self.sent_pairs[pair_key] = time.time()
                    logger.info(f"Marked pair {pair_key} as sent, added to sent_pairs")
                elif not sent and pair_key in self.sent_pairs:
                    del self.sent_pairs[pair_key]
                    logger.info(f"Removed pair {pair_key} from sent_pairs")
        except Exception as e:
            logger.error(f"Error marking post_sent: {e}")
            raise

    def rotate_queues(self, camera_id: int):
        try:
            with self.lock:
                if camera_id in self.start_queues and camera_id in self.end_queues:
                    self.start_queues[camera_id].rotate(-1)
                    self.end_queues[camera_id].rotate(-1)
                    old_pairs = [(k, v) for k, v in self.pair_states.items() if k[0] == camera_id]
                    for (cid, sidx, eidx), _ in old_pairs:
                        del self.pair_states[(cid, sidx, eidx)]
                        self.locked_pairs.discard((cid, sidx, eidx))
                        if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                            del self.active_start_paths[sidx]
                        if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                            del self.active_end_paths[eidx]
                        if (cid, sidx, eidx) in self.retry_counts:
                            del self.retry_counts[(cid, sidx, eidx)]
                    for start_idx in self.available_pairs[camera_id]["starts"]:
                        for end_idx in self.available_pairs[camera_id]["ends"]:
                            self.pair_states[(camera_id, start_idx, end_idx)] = {
                                "timer": None
                            }
                    logger.info(
                        f"Rotated queues for camera {camera_id}, new pairs created, "
                        f"start_queue={list(self.start_queues[camera_id])}, "
                        f"end_queue={list(self.end_queues[camera_id])}, "
                        f"sent_pairs={self.sent_pairs}"
                    )
        except Exception as e:
            logger.error(f"Error rotating queues: {e}")
            raise

    def monitor_pairs(self):
        logger.info("Starting pair monitoring")
        self._last_status_log = 0
        while self.running:
            try:
                with self.lock:
                    # Log trạng thái định kỳ
                    if time.time() - self._last_status_log >= 60:
                        logger.info(
                            f"Current pair_states: {len(self.pair_states)} pairs, "
                            f"sent_pairs: {self.sent_pairs}, "
                            f"active_start_paths: {self.active_start_paths}, "
                            f"active_end_paths: {self.active_end_paths}"
                        )
                        self._last_status_log = time.time()
                        logger.handlers[0].flush()

                    # Tạo available_pairs cho mỗi camera
                    for camera_id in range(len(self.available_pairs)):
                        end_queue = list(self.end_queues[camera_id])
                        start_queue = list(self.start_queues[camera_id])
                        available_pairs = []
                        used_starts = set()
                        used_ends = set()
                        for end_idx in end_queue:
                            if end_idx in used_ends:
                                continue
                            end_camera_id = self.end_task_camera_map.get(end_idx, camera_id)
                            end_state = self.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                            if end_state is False:
                                for start_idx in start_queue:
                                    if start_idx in used_starts:
                                        logger.debug(f"Start path {start_idx} is used, skipping")
                                        continue
                                    start_state = self.state_manager.get_state(camera_id, f"starts_{start_idx}")
                                    pair_key = (camera_id, start_idx, end_idx)
                                    if (
                                        start_state is True and
                                        pair_key in self.pair_states and
                                        pair_key not in self.locked_pairs and
                                        pair_key not in self.sent_pairs
                                    ):
                                        available_pairs.append(pair_key)
                                        used_starts.add(start_idx)
                                        used_ends.add(end_idx)
                                        logger.debug(f"Added pair {pair_key} to available_pairs")
                                        break

                        # Process all pairs in pair_states
                        for pair_key in list(self.pair_states.keys()):
                            cid, sidx, eidx = pair_key
                            if cid != camera_id:
                                continue
                            info = self.pair_states[pair_key]
                            start_state = self.state_manager.get_state(cid, f"starts_{sidx}")
                            end_camera_id = self.end_task_camera_map.get(eidx, cid)
                            end_state = self.state_manager.get_state(end_camera_id, f"ends_{eidx}")
                            elapsed = time.time() - info["timer"] if info["timer"] else 0
                            logger.debug(
                                f"Checking pair ({cid}, {sidx}, {eidx}): "
                                f"start={start_state}, end={end_state}, end_camera={end_camera_id}, "
                                f"timer={elapsed:.2f}s, in_sent_pairs={pair_key in self.sent_pairs}, "
                                f"active_end_paths={self.active_end_paths}, "
                                f"active_start_paths={self.active_start_paths}, "
                                f"retry_counts={self.retry_counts}"
                            )
                            logger.handlers[0].flush()

                            # Start timer
                            if pair_key in available_pairs and info["timer"] is None and pair_key not in self.sent_pairs:
                                self.active_start_paths[sidx] = (cid, eidx)
                                self.active_end_paths[eidx] = (cid, sidx)
                                info["timer"] = time.time()
                                # Re-check state immediately
                                start_state = self.state_manager.get_state(cid, f"starts_{sidx}")
                                end_state = self.state_manager.get_state(end_camera_id, f"ends_{eidx}")
                                if start_state is False or end_state is True:
                                    logger.info(f"Resetting timer for pair ({cid}, {sidx}, {eidx}) due to invalid state after start: start={start_state}, end={end_state}")
                                    info["timer"] = None
                                    if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                        logger.info(f"Releasing start path {sidx} due to invalid state")
                                        del self.active_start_paths[sidx]
                                    if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                        logger.info(f"Releasing end path {eidx} due to invalid state")
                                        del self.active_end_paths[eidx]
                                    self.locked_pairs.discard(pair_key)
                                else:
                                    logger.info(
                                        f"Timer started for camera {cid}, pair ({sidx}, {eidx}), "
                                        f"active_end_paths={self.active_end_paths}, "
                                        f"active_start_paths={self.active_start_paths}"
                                    )

                            # Trigger POST
                            elif (
                                start_state is True and
                                end_state is False and
                                info["timer"] and
                                time.time() - info["timer"] >= 10 and
                                pair_key not in self.sent_pairs
                            ):
                                threading.Thread(
                                    target=delay_post_request,
                                    args=(self, cid, sidx, eidx, self.api_url)
                                ).start()
                                info["timer"] = None
                                logger.info(
                                    f"Triggered delay_post_request for camera {cid}, pair ({sidx}, {eidx})"
                                )

                            # Release locks for sent pairs with invalid states
                            elif (
                                pair_key in self.sent_pairs and
                                (start_state is False or end_state is True)
                            ):
                                logger.info(f"Processing invalid state for sent pair {pair_key}: start={start_state}, end={end_state}")
                                released = False
                                if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                    logger.info(f"Releasing start path {sidx} due to invalid state after POST")
                                    del self.active_start_paths[sidx]
                                    released = True
                                if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                    logger.info(f"Releasing end path {eidx} due to invalid state after POST")
                                    del self.active_end_paths[eidx]
                                    released = True
                                if released:
                                    logger.info(f"Removing pair {pair_key} from sent_pairs due to invalid state")
                                    del self.sent_pairs[pair_key]
                                self.locked_pairs.discard(pair_key)

                            # Timeout for sent pairs
                            elif (
                                pair_key in self.sent_pairs and
                                time.time() - self.sent_pairs[pair_key] >= 300
                            ):
                                logger.info(f"Processing timeout for sent pair {pair_key}")
                                if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                    logger.info(f"Releasing start path {sidx} due to sent pair timeout")
                                    del self.active_start_paths[sidx]
                                if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                    logger.info(f"Releasing end path {eidx} due to sent pair timeout")
                                    del self.active_end_paths[eidx]
                                logger.info(f"Removing pair {pair_key} from sent_pairs due to timeout")
                                del self.sent_pairs[pair_key]
                                self.locked_pairs.discard(pair_key)

                            # Delay reset for invalid states
                            elif (
                                (start_state is False or end_state is True) and
                                info["timer"] and
                                time.time() - info["timer"] < 10
                            ):
                                logger.debug(
                                    f"Delaying reset for pair ({cid}, {sidx}, {eidx}) due to recent timer start"
                                )

                            # Reset for invalid states (non-sent pairs)
                            elif (
                                (start_state is False or end_state is True) and
                                pair_key not in self.sent_pairs
                            ):
                                if info["timer"]:
                                    logger.info(f"Resetting timer for pair ({cid}, {sidx}, {eidx}) due to invalid state: start={start_state}, end={end_state}")
                                info["timer"] = None
                                if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                    logger.info(f"Releasing start path {sidx} due to invalid state")
                                    del self.active_start_paths[sidx]
                                if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                    logger.info(f"Releasing end path {eidx} due to invalid state")
                                    del self.active_end_paths[eidx]
                                self.locked_pairs.discard(pair_key)

                            # Reset stuck timers
                            elif (
                                info["timer"] and
                                time.time() - info["timer"] >= 300 and
                                pair_key not in self.sent_pairs
                            ):
                                logger.warning(f"Resetting stuck timer for pair ({cid}, {sidx}, {eidx}) after 300s")
                                info["timer"] = None
                                if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                    del self.active_start_paths[sidx]
                                if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                    del self.active_end_paths[eidx]
                                self.locked_pairs.discard(pair_key)

                        # Rotate queues
                        all_processed = all(
                            pair_key in self.sent_pairs or (
                                self.state_manager.get_state(camera_id, f"starts_{start_idx}") is False or
                                self.state_manager.get_state(
                                    self.end_task_camera_map.get(end_idx, camera_id), f"ends_{end_idx}"
                                ) is True
                            )
                            for (cid, start_idx, end_idx) in self.pair_states
                            if cid == camera_id
                        )
                        if all_processed:
                            self.rotate_queues(camera_id)
                            logger.info(f"Rotated queues for camera {camera_id} due to all pairs processed")
                            logger.handlers[0].flush()

                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}")
                logger.handlers[0].flush()
                time.sleep(1)