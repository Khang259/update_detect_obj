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
log_handler = logging.FileHandler(f"logs/logs_pair_manager/log_pair_manager_{date_str}.log", encoding='utf-8')
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_pair_manager/logs_errors_pair_manager_{date_str}.log", encoding='utf-8')
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
        self.queue_available_pair = []
        self.used_starts = set()
        self.used_ends = set()
        self.shutdown_event = threading.Event()
        self.thread = threading.Thread(target=self.run)
        self.last_print_time = 0
        self.queue_lock = threading.Lock()
        self.start_times = {}  # {start_idx: timestamp}
        self.end_times = {}    # {end_idx: timestamp}
        self.end_removal_times = {}  # {end_idx: timestamp}
        logger.debug("PairMonitor initialized")

    def start_monitoring(self):
        self.thread.start()
        logger.info("Started PairMonitor")

    def run(self):
        while not self.shutdown_event.is_set():
            current_time = time.time()
            if current_time - self.last_print_time >= 0.5:
                print("PairMonitor is running...")
                self.last_print_time = current_time

            try:
                with self.queue_lock:
                    while not self.pair_monitor_queue.empty():
                        queues = self.pair_monitor_queue.get()
                        start_queue = queues.get("start_queue", [])
                        end_queue = queues.get("end_queue", [])
                        logger.debug(f"Received queues: start={start_queue}, end={end_queue}")

                        # Create new pairs
                        new_pairs = []
                        for pairs in AVAILABLE_PAIRS:
                            valid_starts = []
                            valid_ends = []
                            ready_starts = []
                            ready_ends = []

                            # Lọc các start_idx và end_idx hợp lệ
                            for s in start_queue:
                                if s in pairs["starts"] and s not in self.used_starts:
                                    valid_starts.append(s)
                            for e in end_queue:
                                if e in pairs["ends"] and e not in self.used_ends:
                                    valid_ends.append(e)
                            logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

                            # Cập nhật thời gian xuất hiện chỉ cho valid_starts và valid_ends
                            current_time = time.time()
                            for start_idx in valid_starts:
                                if start_idx not in self.start_times:
                                    self.start_times[start_idx] = current_time
                                    logger.debug(f"Start index {start_idx} added to start_times at {current_time}")

                            for end_idx in valid_ends:
                                if end_idx not in self.end_times:
                                    self.end_times[end_idx] = current_time
                                    logger.debug(f"End index {end_idx} added to end_times at {current_time}")

                            # Cập nhật end_removal_times
                            # for end_idx in list(self.end_removal_times.keys()):
                            #     if end_idx in end_queue:
                            #         del self.end_removal_times[end_idx]
                            #         logger.debug(f"End index {end_idx} reappeared in end_queue, removed from end_removal_times")
                            for end_idx in self.end_times:
                                if end_idx not in end_queue:
                                    self.end_removal_times[end_idx] = current_time
                                    logger.debug(f"End index {end_idx} not in end_queue, added to end_removal_times at {current_time}")

                            # Kiểm tra thời gian tồn tại 5 giây
                            for start_idx in valid_starts:
                                if start_idx in self.start_times:
                                    elapsed = current_time - self.start_times[start_idx]
                                    if elapsed >= 10:
                                        ready_starts.append(start_idx)
                                        logger.debug(f"Start index {start_idx} has lasted {elapsed:.2f}s, added to ready_starts")
                                    else:
                                        logger.warning(f"Start index {start_idx} has lasted {elapsed:.2f}s, not yet 5 seconds")
                                else:
                                    logger.warning(f"Start index {start_idx} not found in start_times")

                            for end_idx in valid_ends:
                                if end_idx in self.end_times:
                                    elapsed = current_time - self.end_times[end_idx]
                                    if elapsed >= 10:
                                        ready_ends.append(end_idx)
                                        logger.debug(f"End index {end_idx} has lasted {elapsed:.2f}s, added to ready_ends")
                                    else:
                                        logger.warning(f"End index {end_idx} has lasted {elapsed:.2f}s, not yet 5 seconds")
                                else:
                                    logger.warning(f"End index {end_idx} not found in end_times")

                            # Tạo cặp từ ready_starts và ready_ends
                            for start_idx, end_idx in zip(ready_starts, ready_ends):
                                if (start_idx, end_idx) not in [p[:2] for p in self.queue_available_pair]:
                                    pair = (start_idx, end_idx, time.time(), False)
                                    new_pairs.append(pair)
                                    self.used_starts.add(start_idx)
                                    self.used_ends.add(end_idx)
                                    logger.info(f"Created new pair: ({start_idx}, {end_idx})")
                                    logger.debug(f"Used starts: {self.used_starts}, Used ends: {self.used_ends}")

                        self.queue_available_pair.extend(new_pairs)
                        logger.debug(f"Updated queue_available_pair: {[(p[0], p[1]) for p in self.queue_available_pair]}")

                    # Check pairs for POST
                    recycle_pairs = []
                    logger.debug(f"Processing recycle_pairs: {[(p[0], p[1]) for p in recycle_pairs]}")
                    for i, pair in enumerate(self.queue_available_pair[:]):
                        start_idx, end_idx, timestamp, mark_post_sent = pair
                        logger.debug(f"Checking health of pair")
                        if not mark_post_sent:
                            logger.info(f"Pair ({start_idx}, {end_idx}) is ready to send POST")
                            data = f"{start_idx},{end_idx}"
                            #self.post_request_manager.trigger_post(data)
                            self.queue_available_pair[i] = (start_idx, end_idx, timestamp, True)
                            logger.info(f"Triggered POST for pair: ({start_idx}, {end_idx})")
                        recycle_pairs.append(self.queue_available_pair[i])
                        logger.debug(f"Recycled pair: ({start_idx}, {end_idx})")

                    # Xóa các cặp nếu end_idx không còn trong end_queue trong 5 giây
                    logger.debug(f"Checking recycle_pairs: {[(p[0], p[1]) for p in recycle_pairs]}")
                    for pair in recycle_pairs[:]:
                        start_idx, end_idx, timestamp, mark_post_sent = pair
                        logger.debug(f"Checking health of pair in recycle_pairs: ({start_idx}, {end_idx})")
                        if end_idx not in end_queue:
                            logger.debug(f"Checking end index {end_idx} for removal")
                            if end_idx in self.end_removal_times:
                                logger.debug(f"End index {end_idx} found in end_removal_times")
                                elapsed = current_time - self.end_removal_times[end_idx]
                                if elapsed >= 5:
                                    self.queue_available_pair.remove(pair)
                                    self.used_starts.discard(start_idx)
                                    self.used_ends.discard(end_idx)
                                    # Reset thời gian của start_idx và end_idx trong self.start_times và self.end_times
                                    if start_idx in self.start_times:
                                        self.start_times[start_idx] = current_time
                                        logger.debug(f"Reset start_idx {start_idx} time to {current_time} in start_times")
                                    else:
                                        self.start_times[start_idx] = current_time
                                        logger.debug(f"Added and reset start_idx {start_idx} time to {current_time} in start_times")
                                    if end_idx in self.end_times:
                                        self.end_times[end_idx] = current_time
                                        logger.debug(f"Reset end_idx {end_idx} time to {current_time} in end_times")
                                    else:
                                        self.end_times[end_idx] = current_time
                                        logger.debug(f"Added and reset end_idx {end_idx} time to {current_time} in end_times")
                                    logger.debug(f"Removed start_idx {start_idx} and end_idx {end_idx} from used_starts and used_ends")
                                    logger.debug(f"Used start, used end after removal{self.used_ends}, {self.used_starts}")
                                    logger.debug(f"Removed start_idx {start_idx} and end_idx {end_idx} from valid_starts and valid_ends")
                                    logger.debug(f"Removed pair ({start_idx}, {end_idx}) from queue_available_pair after {elapsed:.2f}s absence")
                                    del self.end_removal_times[end_idx]
                                else:
                                    logger.debug(f"End index {end_idx} has been absent for {elapsed:.2f}s, not yet 5 seconds")
                            else:
                                self.end_removal_times[end_idx] = current_time
                                logger.debug(f"End index {end_idx} not in end_queue, added to end_removal_times at {current_time}")
                        else:
                            logger.debug(f"End index {end_idx} still in end_queue, no removal needed")

            except queue.Empty:
                logger.debug("pair_monitor_queue is empty, waiting for updates")
            except Exception as e:
                logger.error(f"Error in PairMonitor: {e}")

            time.sleep(0.5)  # Tăng thời gian chờ để giảm tải CPU

    def stop_monitoring(self):
        self.shutdown_event.set()
        self.thread.join()
        logger.info("PairMonitor stopped")