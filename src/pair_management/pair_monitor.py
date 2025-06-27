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
#         self.sent_pairs_queue = sent_pairs_queue  # Keep for compatibility, though not used
#         self.queue_available_pair = []  # (start_idx, end_idx, timestamp, mark_post_sent, initial_start_state, initial_end_state)
#         self.used_starts = set()
#         self.used_ends = set()
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
#                 try:
#                     queues = self.pair_monitor_queue.get_nowait()
#                     start_queue = queues["start_queue"]
#                     end_queue = queues["end_queue"]
#                     logger.debug(f"Received queues: start={[tid for tid in start_queue]}, end={[tid for tid in end_queue]}")

#                     # Remove invalid pairs
#                     to_remove = []
#                     for pair in self.queue_available_pair:
#                         start_idx, end_idx, timestamp, mark_post_sent, initial_start_state, initial_end_state = pair
#                         if start_idx not in start_queue or end_idx not in end_queue:
#                             to_remove.append(pair)
#                             self.used_starts.discard(start_idx)
#                             self.used_ends.discard(end_idx)
#                             logger.debug(f"Removed pair ({start_idx}, {end_idx}) from queue_available_pair")
#                             logger.debug(f"Used starts after removal: {self.used_starts}, used ends after removal: {self.used_ends}")

#                     self.queue_available_pair = [p for p in self.queue_available_pair if p not in to_remove]
#                     logger.debug(f"After cleanup: queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")

#                     # Create new pairs
#                     new_pairs = []
#                     for pairs in AVAILABLE_PAIRS:
#                         valid_starts = [s for s in start_queue if s in pairs["starts"] and s not in self.used_starts]
#                         valid_ends = [e for e in end_queue if e in pairs["ends"] and e not in self.used_ends]
#                         logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

#                         for start_idx, end_idx in zip(valid_starts, valid_ends):
#                             if (start_idx, end_idx) not in [p[:2] for p in self.queue_available_pair]:
#                                 initial_start_state = self.state_manager.states.get(f"starts_{start_idx}", False)
#                                 initial_end_state = self.state_manager.states.get(f"ends_{end_idx}", False)
#                                 pair = (start_idx, end_idx, time.time(), False, initial_start_state, initial_end_state)
#                                 new_pairs.append(pair)
#                                 logger.info(f"Created new pair: ({start_idx}, {end_idx}) with initial states: start={initial_start_state}, end={initial_end_state}")

#                     self.queue_available_pair.extend(new_pairs)
#                     logger.debug(f"Updated queue_available_pair: {[(p[0], p[1]) for p in self.queue_available_pair]}")

#                     # Check pairs for POST and update used_starts/used_ends
#                     for i, pair in enumerate(self.queue_available_pair[:]):
#                         start_idx, end_idx, timestamp, mark_post_sent, initial_start_state, initial_end_state = pair
#                         current_start_state = self.state_manager.states.get(f"starts_{start_idx}", False)
#                         current_end_state = self.state_manager.states.get(f"ends_{end_idx}", False)
#                         elapsed = time.time() - timestamp

#                         # Check if states have not changed and elapsed >= 15s to add to used_starts/used_ends
#                         if elapsed >= 15 and current_start_state == initial_start_state and current_end_state == initial_end_state:
#                             if start_idx not in self.used_starts:
#                                 self.used_starts.add(start_idx)
#                                 logger.debug(f"Added {start_idx} to used_starts after 15s with unchanged state")
#                             if end_idx not in self.used_ends:
#                                 self.used_ends.add(end_idx)
#                                 logger.debug(f"Added {end_idx} to used_ends after 15s with unchanged state")

#                         # Trigger POST if elapsed >= 15s and not sent
#                         if elapsed >= 15 and not mark_post_sent:
#                             logger.info(f"Pair ({start_idx}, {end_idx}) is ready to send POST after {elapsed:.2f}s")
#                             data = f"{start_idx},{end_idx}"
#                             self.post_request_manager.trigger_post(data)
#                             self.queue_available_pair[i] = (start_idx, end_idx, timestamp, True, initial_start_state, initial_end_state)
#                             logger.info(f"Triggered POST for pair: ({start_idx}, {end_idx})")

#                 except queue.Empty:
#                     pass

#             except Exception as e:
#                 logger.error(f"Error in PairMonitor: {e}")

#             time.sleep(0.1)

#     def stop_monitoring(self):
#         self.shutdown_event.set()
#         self.thread.join()
#         logger.info("PairMonitor stopped")