import logging
import time
import threading
from queue import Queue
from datetime import datetime
import os
import queue
from src.config.config import AVAILABLE_PAIRS
from src.state_manager.state_manager import StateManager
from src.post_request.post_request import PostRequestManager

date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_pair_manager", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_pair_manager", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_pair_manager/log_pair_manager_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_pair_manager/logs_errors_pair_manager_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("pair_manager")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class PairMonitor:
    def __init__(self, state_manager: StateManager, post_request_manager: PostRequestManager, pair_monitor_queue: Queue, sent_pairs_queue: Queue):
        self.state_manager = state_manager
        self.post_request_manager = post_request_manager
        self.pair_monitor_queue = pair_monitor_queue
        self.sent_pairs_queue = sent_pairs_queue
        self.queue_available_pair = []  # (start_idx, end_idx, timestamp, mark_post_sent)
        self.shutdown_event = threading.Event()
        self.thread = threading.Thread(target=self.run)
        logger.debug("PairMonitor initialized")

    def start_monitoring(self):
        self.thread.start()
        logger.info("Started PairMonitor")

    def run(self):
        while not self.shutdown_event.is_set():
            print("PairMonitor is running...")
            try:
                # Xử lý các cặp đã gửi POST
                while not self.sent_pairs_queue.empty():
                    start_idx, end_idx, success = self.sent_pairs_queue.get()
                    for i, pair in enumerate(self.queue_available_pair):
                        if pair[:2] == (start_idx, end_idx):
                            self.queue_available_pair[i] = (start_idx, end_idx, pair[2], success)
                            logger.debug(f"Updated pair ({start_idx}, {end_idx}) with mark_post_sent={success}")

                # Xử lý hàng đợi từ queue_manager
                try:
                    queues = self.pair_monitor_queue.get_nowait()  # Non-blocking
                    start_queue = queues["start_queue"]
                    end_queue = queues["end_queue"]
                    logger.debug(f"Received queues: start={start_queue}, end={end_queue}")

                    # Tạo các cặp mới theo AVAILABLE_PAIRS
                    new_pairs = []
                    for pairs in AVAILABLE_PAIRS:
                        valid_starts = [s[1] for s in start_queue if s[1] in pairs["starts"]]
                        valid_ends = [e[1] for e in end_queue if e[1] in pairs["ends"]]
                        logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

                        temp_starts = valid_starts.copy()
                        temp_ends = valid_ends.copy()
                        for start_idx, end_idx in zip(temp_starts, temp_ends):
                            pair = (start_idx, end_idx, time.time(), False)
                            logger.debug(f"Checking pair: {pair[:2]}")
                            if pair[:2] not in [p[:2] for p in self.queue_available_pair]:
                                new_pairs.append(pair)
                                logger.debug(f"Added pair: {pair[:2]}")
                                if start_idx in valid_starts:
                                    valid_starts.remove(start_idx)
                                if end_idx in valid_ends:
                                    valid_ends.remove(end_idx)

                    self.queue_available_pair.extend(new_pairs)
                except queue.Empty:
                    pass  # Không có dữ liệu mới, tiếp tục kiểm tra cặp hiện có

                # Kiểm tra thời gian và trạng thái
                to_remove = []
                for pair in self.queue_available_pair[:]:
                    start_idx, end_idx, timestamp, mark_post_sent = pair
                    start_camera_id = next((cid for cid, tid in start_queue if tid == start_idx), None)
                    end_camera_id = next((cid for cid, tid in end_queue if tid == end_idx), None)
                    start_state = self.state_manager.states.get((start_camera_id, f"starts_{start_idx}"), False) if start_camera_id is not None else False
                    end_state = self.state_manager.states.get((end_camera_id, f"ends_{end_idx}"), False) if end_camera_id is not None else False
                    elapsed = time.time() - timestamp
                    logger.debug(f"Pair: ({start_idx}, {end_idx}), start_state: {start_state}, end_state: {end_state}, elapsed: {elapsed:.2f}s, mark_post_sent: {mark_post_sent}")

                    if start_state and not end_state and elapsed >= 15 and not mark_post_sent:
                        logger.info(f"Pair ({start_idx}, {end_idx}) is ready to send POST")
                        data = f"{start_idx},{end_idx}"
                        self.post_request_manager.trigger_post(data)
                        logger.info(f"Triggered POST for pair: ({start_idx}, {end_idx})")
                    elif end_state:
                        to_remove.append(pair)
                        logger.debug(f"Removing pair due to end_state=True: {pair[:2]}")
                    elif not start_state:
                        to_remove.append(pair)
                        logger.debug(f"Removing pair due to start_state=False: {pair[:2]}")

                # Xóa các cặp không hợp lệ
                for pair in to_remove:
                    self.queue_available_pair.remove(pair)
                    logger.info(f"Removed pair: {pair[:2]}")

            except Exception as e:
                logger.error(f"Error in PairMonitor: {e}")

            time.sleep(0.1)  # Tránh CPU overload

    def stop_monitoring(self):
        self.shutdown_event.set()
        self.thread.join()
        logger.info("PairMonitor stopped")