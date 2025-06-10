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
        self.running = True
        self.lock = threading.Lock()
        self.start_queues = {}
        self.end_queues = {}
        self.pair_states = {}
        self.locked_pairs = set()
        self.active_end_paths = {}  # {end_idx: (camera_id, start_idx)}
        self.active_start_paths = {}  # {start_idx: (camera_id, end_idx)}
        self.retry_counts = {}  # {pair_key: retry_count}
        self.end_task_camera_map = {
            "10000170": 2, "10000171": 2, "10000140": 2, "10000141": 2,  # Camera 3
            "10000164": 0,  # Camera 1
            "10000147": 1   # Camera 2
        }
        try:
            for camera_id in range(len(available_pairs)):
                self.start_queues[camera_id] = deque(available_pairs[camera_id]["starts"])
                self.end_queues[camera_id] = deque(available_pairs[camera_id]["ends"])
                for start_idx in available_pairs[camera_id]["starts"]:
                    for end_idx in available_pairs[camera_id]["ends"]:
                        self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}
            logger.info("PairManager initialized with available pairs")
        except Exception as e:
            logger.error(f"Error initializing PairManager: {e}")
            raise

    def mark_post_sent(self, camera_id: int, start_idx: str, end_idx: str, value: bool, success: bool = True):
        try:
            with self.lock:
                pair_key = (camera_id, start_idx, end_idx)
                self.pair_states[pair_key]["post_sent"] = value
                if value and success:
                    self.locked_pairs.add(pair_key)
                    self.active_end_paths[end_idx] = (camera_id, start_idx)
                    self.active_start_paths[start_idx] = (camera_id, end_idx)
                    if pair_key in self.retry_counts:
                        del self.retry_counts[pair_key]
                else:
                    self.locked_pairs.discard(pair_key)
                    if end_idx in self.active_end_paths and self.active_end_paths[end_idx] == (camera_id, start_idx):
                        del self.active_end_paths[end_idx]
                    if start_idx in self.active_start_paths and self.active_start_paths[start_idx] == (camera_id, end_idx):
                        del self.active_start_paths[start_idx]
                    if not success and pair_key in self.retry_counts and self.retry_counts[pair_key] >= 3:
                        del self.retry_counts[pair_key]
                logger.info(
                    f"Marked post_sent={value} for camera {camera_id}, pair ({start_idx}, {end_idx}), "
                    f"success={success}, active_end_paths={self.active_end_paths}, "
                    f"active_start_paths={self.active_start_paths}, retry_counts={self.retry_counts}"
                )
        except Exception as e:
            logger.error(f"Error marking post_sent: {e}")
            raise

    def rotate_queues(self, camera_id: int):
        try:
            with self.lock:
                if camera_id in self.start_queues and camera_id in self.end_queues:
                    # Rotate if any pair is processed or invalid
                    any_processed = any(
                        info["post_sent"] or (
                            self.state_manager.get_state(camera_id, f"starts_{start_idx}") is False or
                            self.state_manager.get_state(
                                self.end_task_camera_map.get(end_idx, camera_id), f"ends_{end_idx}"
                            ) is True
                        )
                        for (cid, start_idx, end_idx), info in self.pair_states.items()
                        if cid == camera_id
                    )
                    if any_processed:
                        self.start_queues[camera_id].rotate(-1)
                        self.end_queues[camera_id].rotate(-1)
                        old_pairs = [(k, v) for k, v in self.pair_states.items() if k[0] == camera_id]
                        for (cid, sidx, eidx), _ in old_pairs:
                            del self.pair_states[(cid, sidx, eidx)]
                            self.locked_pairs.discard((cid, sidx, eidx))
                            if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                del self.active_end_paths[eidx]
                            if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                del self.active_start_paths[sidx]
                            if (cid, sidx, eidx) in self.retry_counts:
                                del self.retry_counts[(cid, sidx, eidx)]
                        for start_idx in self.available_pairs[camera_id]["starts"]:
                            for end_idx in self.available_pairs[camera_id]["ends"]:
                                self.pair_states[(camera_id, start_idx, end_idx)] = {"post_sent": False, "timer": None}
                        logger.info(
                            f"Rotated queues for camera {camera_id}, new pairs created, "
                            f"active_end_paths={self.active_end_paths}, active_start_paths={self.active_start_paths}"
                        )
        except Exception as e:
            logger.error(f"Error rotating queues: {e}")
            raise

    def monitor_pairs(self):
        logger.info("Starting pair monitoring")
        while self.running:
            try:
                #Duyệt từng phần tử trong available_pair
                for camera_id in range(len(self.available_pairs)):
                    with self.lock:
                        end_queue = list(self.end_queues[camera_id])
                        start_queue = list(self.start_queues[camera_id])
                        available_pairs = []
                        used_starts = set()
                        #Duyệt từng phần tử trong end_queue
                        for end_idx in end_queue:
                            #với từng tử trong end_task_camera_map sẽ được gán định danh là end_camera_id
                            end_camera_id = self.end_task_camera_map.get(end_idx, camera_id)
                            #Lấy state của end path 
                            end_state = self.state_manager.get_state(end_camera_id, f"ends_{end_idx}")
                            #Kiểm tra state của end path không có hàng = False 
                            if end_state is False:
                                #Duyệt qua các start path trong start_queue
                                for start_idx in start_queue:
                                    #Nếu start path đã được sử dụng (nằm trong used start)
                                    if start_idx in used_starts:
                                        #In log debug và tiếp tục chương trình 
                                        logger.debug(f"Start path {start_idx} is used, skipping")
                                        continue
                                    #Nếu start path không nằm trong used start, lấy trạng thái của start_ state
                                    start_state = self.state_manager.get_state(camera_id, f"starts_{start_idx}")
                                    #Khai báo khóa định dang cho start và end path 
                                    pair_key = (camera_id, start_idx, end_idx)
                                    #Nếu
                                    if (
                                        #trạng thái start path = True (có hàng) 
                                        start_state is True and
                                        #và khóa định danh nằm trong khóa trạng thái 
                                        pair_key in self.pair_states and
                                        # và trạng thái của khóa định dang là False(post_sent = False(chưa gửi))
                                        not self.pair_states[pair_key]["post_sent"] and
                                        #và khóa định danh không nằm trong locked_pair
                                        pair_key not in self.locked_pairs
                                    ):
                                        #thì sẽ cập nhật khóa định danh đó vào cặp hợp lệ 
                                        available_pairs.append(pair_key)
                                        #và thêm start path vào list used_starts
                                        used_starts.add(start_idx)
                                        break  # One start per end

                        # Process all pairs for timer checks and state validation
                        #Duyệt từng khóa định danh trong list khóa trạng thái 
                        for pair_key in list(self.pair_states.keys()):
                            #Khai báo cid, sidx, eidx với khóa định danhm để debug
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
                                f"start={start_state}, end={end_state},"
                                f"post_sent={info['post_sent']}, timer={elapsed:.2f}s, "
                                f"active_end_paths={self.active_end_paths}, "
                                f"active_start_paths={self.active_start_paths}, "
                                f"retry_counts={self.retry_counts}"
                            )

                            # Start timer for new valid pairs
                            if pair_key in available_pairs and info["timer"] is None:
                                self.active_start_paths[sidx] = (cid, eidx)
                                self.active_end_paths[eidx] = (cid, sidx)
                                info["timer"] = time.time()
                                logger.info(
                                    f"Timer started for camera {cid}, pair ({sidx}, {eidx}), "
                                    f"active_end_paths={self.active_end_paths}, "
                                    f"active_start_paths={self.active_start_paths}"
                                    f"timer = {time.time() - info["timer"]}"
                                )
                            # Trigger POST for pairs with timer >= 10s
                            elif (
                                start_state is True and
                                end_state is False and
                                not info["post_sent"] and
                                info["timer"] and
                                time.time() - info["timer"] >= 10
                            ):
                                threading.Thread(
                                    target=delay_post_request,
                                    args=(self, cid, sidx, eidx, self.api_url)
                                ).start()
                                info["timer"] = None
                                logger.info(
                                    f"Triggered delay_post_request for camera {cid}, pair ({sidx}, {eidx})"
                                )
                            # Release locks if states are invalid
                            elif (
                                (start_state is False or end_state is True)
                            ):
                                if sidx in self.active_start_paths and self.active_start_paths[sidx] == (cid, eidx):
                                    logger.info(f"Releasing start path {sidx} due to invalid state")
                                    del self.active_start_paths[sidx]
                                if eidx in self.active_end_paths and self.active_end_paths[eidx] == (cid, sidx):
                                    logger.info(f"Releasing end path {eidx} due to invalid state")
                                    del self.active_end_paths[eidx]
                                info["timer"] = None
                                self.locked_pairs.discard(pair_key)

                    # Rotate queues if all pairs are processed
                    self.rotate_queues(camera_id)
                    logger.info(f"Rotate queues just happened: {self.rotate_queues()}")

                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in monitor_pairs: {e}")
                time.sleep(1)