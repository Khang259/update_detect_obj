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
logger.setLevel(logging.INFO)
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
        self.pending_pairs = {}  # Store pending pairs with their timestamps
        self.sent_pairs_end_state_timestamps = {}  # Store timestamps when end_state becomes True
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

                    # Remove invalid pairs (only for non-sent pairs)
                    # to_remove = []
                    # for pair in self.queue_available_pair:
                    #     start_idx, end_idx, timestamp, mark_post_sent = pair
                    #     if not mark_post_sent and end_idx not in end_queue:
                    #         to_remove.append(pair)
                    #         self.used_starts.discard(start_idx)
                    #         self.used_ends.discard(end_idx)
                    #         logger.debug(f"Removed non-sent pair ({start_idx}, {end_idx}) from queue_available_pair")

                    # self.queue_available_pair = [p for p in self.queue_available_pair if p not in to_remove]
                    # logger.debug(f"After cleanup: queue_available_pair={[(p[0], p[1]) for p in self.queue_available_pair]}")

                    # Track potential new pairs
                    for pairs in AVAILABLE_PAIRS:
                        valid_starts = [s for s in start_queue if s in pairs["starts"] and s not in self.used_starts]
                        valid_ends = [e for e in end_queue if e in pairs["ends"] and e not in self.used_ends]
                        logger.debug(f"For AVAILABLE_PAIRS entry: valid_starts={valid_starts}, valid_ends={valid_ends}")

                        for start_idx, end_idx in zip(valid_starts, valid_ends):
                            pair_key = (start_idx, end_idx)
                            if pair_key not in [p[:2] for p in self.queue_available_pair] and pair_key not in self.pending_pairs:
                                self.pending_pairs[pair_key] = time.time()
                                logger.debug(f"Tracking new pending pair: ({start_idx}, {end_idx}), {time.time()}")

                    # Check pending pairs
                    new_pairs = []
                    for pair_key, timestamp in list(self.pending_pairs.items()):
                        start_idx, end_idx = pair_key
                        elapsed = time.time() - timestamp
                        logger.debug(f"Checking pending pair: ({start_idx}, {end_idx}), elapsed={elapsed:.2f}s")
                        if elapsed >= 5:
                            pair = (start_idx, end_idx, time.time(), True)
                            new_pairs.append(pair)
                            self.used_starts.add(start_idx)
                            self.used_ends.add(end_idx)
                            data = f"{start_idx},{end_idx}"
                            self.post_request_manager.trigger_post(data)
                            self.sent_pairs_queue.put(pair)
                            logger.info(f"Created and sent POST for pair: ({start_idx}, {end_idx})")
                            del self.pending_pairs[pair_key]

                    self.queue_available_pair.extend(new_pairs)
                    logger.debug(f"Updated queue_available_pair: {[(p[0], p[1]) for p in self.queue_available_pair]}")

                    # Clean up pending pairs that are no longer valid
                    # for pair_key in list(self.pending_pairs.keys()):
                    #     start_idx, end_idx = pair_key
                    #     if start_idx not in start_queue or end_idx not in end_queue:
                    #         del self.pending_pairs[pair_key]
                    #         logger.debug(f"Removed invalid pending pair: ({start_idx}, {end_idx})")

                    # Check sent pairs for end_state
                    for i, pair in enumerate(self.queue_available_pair[:]):
                        start_idx, end_idx, timestamp, mark_post_sent = pair
                        logger.debug(f"Checking sent pair: ({start_idx}, {end_idx}), mark_post_sent={mark_post_sent}")
                        if mark_post_sent:
                            pair_key = (start_idx, end_idx)
                            end_state = end_idx not in end_queue  # True if end_idx not in end_queue, False otherwise
                            logger.debug(f"State for end_idx {end_idx}: {end_state} (derived from end_queue)")

                            if end_state:
                                logger.debug(f"Pair ({start_idx}, {end_idx}) has end_state True")
                                # If end_state is True, record or update timestamp
                                if pair_key not in self.sent_pairs_end_state_timestamps:
                                    self.sent_pairs_end_state_timestamps[pair_key] = time.time()
                                    logger.debug(f"Started tracking end_state True for pair: ({start_idx}, {end_idx}) at {time.time()}")
                                else:
                                    elapsed = time.time() - self.sent_pairs_end_state_timestamps[pair_key]
                                    logger.debug(f"Pair ({start_idx}, {end_idx}) end_state True, elapsed={elapsed:.2f}s")
                                    if elapsed >= 5:  # Wait 5 seconds before removing
                                        self.used_starts.discard(start_idx)
                                        self.used_ends.discard(end_idx)
                                        logger.debug(f"Used starts and ends after end_state: ({self.used_starts}, {self.used_ends})")
                                        self.queue_available_pair.pop(i)
                                        logger.info(f"Removed sent pair with end_state True after 5s: ({start_idx}, {end_idx})")
                                        del self.sent_pairs_end_state_timestamps[pair_key]
                            # else:
                            #     # If end_state is False, remove timestamp if it exists
                            #     if pair_key in self.sent_pairs_end_state_timestamps:
                            #         del self.sent_pairs_end_state_timestamps[pair_key]
                            #         logger.debug(f"Stopped tracking end_state for pair: ({start_idx}, {end_idx}) as end_state is False")

                except queue.Empty:
                    pass

            except Exception as e:
                logger.error(f"Error in PairMonitor: {e}")

            time.sleep(0.1)

    def stop_monitoring(self):
        self.shutdown_event.set()
        self.thread.join()
        logger.info("PairMonitor stopped")