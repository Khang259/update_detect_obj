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
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("pair_manager")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class PairManager:
    def __init__(self, available_pairs, state_manager, api_url):
        self.available_pairs = available_pairs
        self.state_manager = state_manager
        self.api_url = api_url
        self.running = True
        self.lock = threading.Lock()
        self.start_queues = {}
        self.end_queues = {}
        self.pair_states = {}
        self.locked_pairs = set()  # Track locked pairs
        try:
            for camera_id in range(len(available_pairs)):
                self.start_queues[camera_id] = deque(available_pairs[camera_id]["starts"])
                self.end_queues[camera_id] = deque(available_pairs[camera_id]["ends"])
                if self.start_queues[camera_id] and self.end_queues[camera_id]:
                    start_idx = self.start_queues[camera_id][0]
                    end_idx = self.end_queues[camera_id][0]
                    self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}
            logger.info("PairManager initialized with available pairs")
        except Exception as e:
            logger.error(f"Error initializing PairManager: {e}")
            raise

    def mark_post_sent(self, camera_id: int, start_idx: str, end_idx: str, value: bool):
        try:
            with self.lock:
                self.pair_states[(camera_id, start_idx, end_idx)]["post_sent"] = value
                if value:
                    self.locked_pairs.add((camera_id, start_idx, end_idx))
                else:
                    self.locked_pairs.discard((camera_id, start_idx, end_idx))
                logger.info(f"Marked post_sent={value} for camera {camera_id}, pair ({start_idx}, {end_idx})")
        except Exception as e:
            logger.error(f"Error marking post_sent for camera {camera_id}, pair ({start_idx}, {end_idx}): {e}")
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
                    if self.start_queues[camera_id] and self.end_queues[camera_id]:
                        start_idx = self.start_queues[camera_id][0]
                        end_idx = self.end_queues[camera_id][0]
                        self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}
                        logger.info(f"Rotated queues for camera {camera_id}, new pair: ({start_idx}, {end_idx})")
        except Exception as e:
            logger.error(f"Error rotating queues for camera {camera_id}: {e}")
            raise

    def monitor_pairs(self):
        logger.info("Starting pair monitoring")
        while self.running:
            try:
                for (camera_id, start_idx, end_idx), info in list(self.pair_states.items()):
                    if (camera_id, start_idx, end_idx) in self.locked_pairs:
                        continue  # Skip locked pairs
                    start_state = self.state_manager.get_state(camera_id, f"starts_{start_idx}")
                    end_state = self.state_manager.get_state(camera_id, f"ends_{end_idx}")
                    logger.debug(f"Checking pair ({camera_id}, {start_idx}, {end_idx}): start={start_state}, end={end_state}")

                    if start_state is True and end_state is False and not info["post_sent"]:
                        if info["timer"] is None:
                            info["timer"] = time.time()
                            logger.info(f"Timer started for camera {camera_id}, pair ({start_idx}, {end_idx})")
                        elif time.time() - info["timer"] >= 10:
                            threading.Thread(
                                target=delay_post_request,
                                args=(self, camera_id, start_idx, end_idx, self.api_url)
                            ).start()
                            info["timer"] = None
                    else:
                        if info["timer"] is not None:
                            logger.info(f"Reset timer for camera {camera_id}, pair ({start_idx}, {end_idx})")
                        info["timer"] = None
                        if info["post_sent"] and (start_state is False or end_state is True):
                            self.mark_post_sent(camera_id, start_idx, end_idx, False)

                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}")
                time.sleep(1)