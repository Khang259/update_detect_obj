# #pair_monitor.py
# import logging
# import time
# import threading
# from queue import Queue
# from datetime import datetime
# import os
# import queue
# from src.config.config import AVAILABLE_PAIRS
# from src.state_manager.state_manager import StateManager
# from src.post_request.post_request import PostRequestManager

# date_str = datetime.now().strftime("%Y%m%d")
# os.makedirs("logs/logs_pair_manager", exist_ok=True)
# os.makedirs("logs/logs_errors/logs_errors_pair_manager", exist_ok=True)

# log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# log_handler = logging.FileHandler(f"logs/logs_pair_manager/log_pair_manager_{date_str}.log", encoding='utf-8')
# log_handler.setFormatter(log_formatter)
# error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_pair_manager/logs_errors_pair_manager_{date_str}.log", encoding='utf-8')
# error_handler.setFormatter(log_formatter)
# error_handler.setLevel(logging.ERROR)

# logger = logging.getLogger("pair_manager")
# logger.setLevel(logging.DEBUG)
# logger.addHandler(log_handler)
# logger.addHandler(error_handler)

# class PairMonitor:
#     def __init__(self, state_manager: StateManager, post_request_manager: PostRequestManager, pair_monitor_queue: Queue, sent_pairs_queue: Queue):
#         self.state_manager = state_manager
#         self.post_request_manager = post_request_manager
#         self.pair_monitor_queue = pair_monitor_queue
#         self.sent_pairs_queue = sent_pairs_queue
#         self.queue_available_pair = []  # (start_idx, end_idx, timestamp, mark_post_sent)
#         self.sent_pairs = set()  # Theo dõi các cặp đã gửi POST thành công
#         self.used_starts = set()  # Theo dõi start_idx đã được ghép
#         self.used_ends = set()    # Theo dõi end_idx đã được ghép
#         self.shutdown_event = threading.Event()
#         self.thread = threading.Thread(target=self.run)
#         self.last_print_time = 0
#         logger.debug("PairMonitor initialized")

#     def start_monitoring(self):
#         self.thread.start()
#         logger.info("Started PairMonitor")

#     def run(self):
#         while not self.shutdown_event.is_set():
#             current_time = time.time()
#             if current_time - self.last_print_time >= 0.5:
#                 print("PairMonitor is running...")
#                 self.last_print_time = current_time

#             try:
#                 # Xử lý các cặp đã gửi POST
#                 while not self.sent_pairs_queue.empty():
#                     start_idx, end_idx, success = self.sent_pairs_queue.get()
#                     logger.debug(f"Processing sent pair: ({start_idx}, {end_idx}), success={success}, queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")
#                     for i, pair in enumerate(self.queue_available_pair[:]):
#                         if pair[:2] == (start_idx, end_idx):
#                             self.queue_available_pair[i] = (start_idx, end_idx, pair[2], success)
#                             logger.debug(f"Updated pair ({start_idx}, {end_idx}) with mark_post_sent={success}, timestamp={pair[2]}")
#                             if success:
#                                 self.sent_pairs.add((start_idx, end_idx))
#                                 logger.debug(f"Added ({start_idx}, {end_idx}) to sent_pairs")
#                                 start_camera_id = None
#                                 end_camera_id = None
#                                 if 'start_queue' in locals() and 'end_queue' in locals():
#                                     start_camera_id = next((cid for cid, tid in start_queue if tid == start_idx), None)
#                                     end_camera_id = next((cid for cid, tid in end_queue if tid == end_idx), None)
#                                 start_state = self.state_manager.states.get((start_camera_id, f"starts_{start_idx}"), False) if start_camera_id is not None else False
#                                 end_state = self.state_manager.states.get((end_camera_id, f"ends_{end_idx}"), False) if end_camera_id is not None else False
#                                 if not start_state:
#                                     self.used_starts.discard(start_idx)
#                                     logger.debug(f"Removed {start_idx} from used_starts due to start_state={start_state} after POST success")
#                                 if end_state:
#                                     self.used_ends.discard(end_idx)
#                                     self.used_starts.discard(start_idx)
#                                     logger.debug(f"Removed {end_idx} from used_ends due to end_state={end_state} after POST success")
#                                     # Xóa cặp vì cả start_idx và end_idx đã bị discard
#                                     self.queue_available_pair = [p for p in self.queue_available_pair if p[:2] != (start_idx, end_idx)]
#                                     logger.debug(f"Removed pair ({start_idx}, {end_idx}) from queue_available_pair after POST success and discard")

#                 # Xử lý hàng đợi từ queue_manager
#                 try:
#                     queues = self.pair_monitor_queue.get_nowait()
#                     start_queue = queues["start_queue"]
#                     end_queue = queues["end_queue"]
#                     # logger.info(f"Start queue task_ids: {[s[1] for s in start_queue]}")
#                     # logger.info(f"End queue task_ids: {[e[1] for e in end_queue]}")
#                     # logger.debug(f"Received queues: start={start_queue}, end={end_queue}")

#                     new_pairs = []
#                     for pairs in AVAILABLE_PAIRS:
#                         valid_starts = [s[1] for s in start_queue if s[1] in pairs["starts"] and s[1] not in self.used_starts]
#                         valid_ends = [e[1] for e in end_queue if e[1] in pairs["ends"] and e[1] not in self.used_ends]
#                         # logger.debug(f"used_starts / ends: {self.used_starts}, {self.used_ends}")
#                         # logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

#                         for start_idx, end_idx in zip(valid_starts, valid_ends):
#                             if (start_idx, end_idx) not in self.sent_pairs:
#                                 pair = (start_idx, end_idx, time.time(), False)
#                                 logger.info(f"Checking pair: {pair[:2]}")
#                                 if pair[:2] not in [p[:2] for p in self.queue_available_pair]:
#                                     new_pairs.append(pair)
#                                     # logger.debug(f"Added pair: {pair[:2]}")
#                                     self.used_starts.add(start_idx)
#                                     self.used_ends.add(end_idx)
#                                     # logger.debug(f"Added ({start_idx}, {end_idx}) to used_starts and used_ends")

#                     self.queue_available_pair.extend(new_pairs)
#                 except queue.Empty:
#                     pass

#                 # Kiểm tra thời gian và trạng thái
#                 for i, pair in enumerate(self.queue_available_pair[:]):
#                     start_idx, end_idx, timestamp, mark_post_sent = pair
#                     start_camera_id = next((cid for cid, tid in start_queue if tid == start_idx), None) if 'start_queue' in locals() else None
#                     end_camera_id = next((cid for cid, tid in end_queue if tid == end_idx), None) if 'end_queue' in locals() else None
#                     start_state = self.state_manager.states.get((start_camera_id, f"starts_{start_idx}"), False) if start_camera_id is not None else False
#                     end_state = self.state_manager.states.get((end_camera_id, f"ends_{end_idx}"), False) if end_camera_id is not None else False
#                     elapsed = time.time() - timestamp
#                    #logger.debug(f"Pair: ({start_idx}, {end_idx}), start_state: {start_state}, end_state: {end_state}, elapsed: {elapsed:.2f}s, mark_post_sent: {mark_post_sent}")
#                     to_remove = []
#                     if start_state and not end_state and elapsed >= 15 and not mark_post_sent:
#                         logger.info(f"Pair ({start_idx}, {end_idx}) is ready to send POST")
#                         data = f"{start_idx},{end_idx}"
#                         self.post_request_manager.trigger_post(data)
#                         self.queue_available_pair[i] = (start_idx, end_idx, timestamp, True) 
#                         logger.info(f"Triggered POST for pair: ({start_idx}, {end_idx})")
#                         logger.debug(f"POST triggered for pair: ({start_idx}, {end_idx}), waiting for confirmation")
#                     elif end_state or not start_state:
#                         start_discarded = False
#                         end_discarded = False
#                         # if not start_state:
#                         #     self.used_starts.discard(start_idx)
#                         #     start_discarded = True
#                         #     logger.debug(f"Discarded {start_idx} from used_starts due to start_state={start_state}")
#                         if end_state:
#                             self.used_ends.discard(end_idx)
#                             end_discarded = True
#                             logger.debug(f"Discarded {end_idx} from used_ends due to end_state={end_state}")
#                         if start_discarded and end_discarded:
#                             to_remove.append(pair)
#                             logger.debug(f"Removed pair ({start_idx}, {end_idx}) from queue_available_pair due to both start_idx and end_idx discarded")

#                 # Xóa các cặp không hợp lệ
#                 # logger.debug(f"Before removal: queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")
#                 self.queue_available_pair = [p for p in self.queue_available_pair if p not in to_remove]
#                 # logger.debug(f"After removal: queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")

#             except Exception as e:
#                 logger.error(f"Error in PairMonitor: {e}")

#             time.sleep(0.1)

#     def stop_monitoring(self):
#         self.shutdown_event.set()
#         self.thread.join()
#         logger.info("PairMonitor stopped")

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
                try:
                    queues = self.pair_monitor_queue.get_nowait()
                    start_queue = queues["start_queue"]
                    end_queue = queues["end_queue"]
                    logger.debug(f"Received queues: start={[tid for tid in start_queue]}, end={[tid for tid in end_queue]}")

                    # Remove invalid pairs
                    to_remove = []
                    for pair in self.queue_available_pair:
                        start_idx, end_idx, timestamp, mark_post_sent = pair
                        if start_idx not in start_queue or end_idx not in end_queue:
                            to_remove.append(pair)
                            self.used_starts.discard(start_idx)
                            self.used_ends.discard(end_idx)
                            logger.debug(f"Removed pair ({start_idx}, {end_idx}) from queue_available_pair")

                    self.queue_available_pair = [p for p in self.queue_available_pair if p not in to_remove]
                    logger.debug(f"After cleanup: queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")

                    # Create new pairs
                    new_pairs = []
                    for pairs in AVAILABLE_PAIRS:
                        valid_starts = [s for s in start_queue if s in pairs["starts"] and s not in self.used_starts]
                        valid_ends = [e for e in end_queue if e in pairs["ends"] and e not in self.used_ends]
                        logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

                        for start_idx, end_idx in zip(valid_starts, valid_ends):
                            if (start_idx, end_idx) not in [p[:2] for p in self.queue_available_pair]:
                                pair = (start_idx, end_idx, time.time(), False)
                                new_pairs.append(pair)
                                self.used_starts.add(start_idx)
                                self.used_ends.add(end_idx)
                                logger.info(f"Created new pair: ({start_idx}, {end_idx})")

                    self.queue_available_pair.extend(new_pairs)
                    logger.debug(f"Updated queue_available_pair: {[(p[0], p[1]) for p in self.queue_available_pair]}")

                except queue.Empty:
                    pass

                # Check pairs for POST
                for i, pair in enumerate(self.queue_available_pair[:]):
                    start_idx, end_idx, timestamp, mark_post_sent = pair
                    elapsed = time.time() - timestamp
                    if elapsed >= 15 and not mark_post_sent:
                        logger.info(f"Pair ({start_idx}, {end_idx}) is ready to send POST after {elapsed:.2f}s")
                        data = f"{start_idx},{end_idx}"
                        self.post_request_manager.trigger_post(data)
                        self.queue_available_pair[i] = (start_idx, end_idx, timestamp, True)
                        logger.info(f"Triggered POST for pair: ({start_idx}, {end_idx})")

            except Exception as e:
                logger.error(f"Error in PairMonitor: {e}")

            time.sleep(0.1)

    def stop_monitoring(self):
        self.shutdown_event.set()
        self.thread.join()
        logger.info("PairMonitor stopped")