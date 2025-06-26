import logging
import threading
from queue import Queue
import queue
import os
from datetime import datetime
from collections import deque
from src.config.config import START_TASK_PATHS, END_TASK_PATHS

date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_queue_manager", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_queue_manager", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_queue_manager/log_queue_manager_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_queue_manager/logs_errors_queue_manager_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("queue_manager")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class QueueManager:
    def __init__(self, queue_manager_queue: Queue, pair_monitor_queue: Queue):
        self.start_queue = deque()
        self.end_queue = deque()
        self.queue_manager_queue = queue_manager_queue
        self.pair_monitor_queue = pair_monitor_queue
        self.prev_states = {}
        logger.info(f"QueueManager initialized with queue_manager_queue id: {id(self.queue_manager_queue)}")

    def process_state_updates(self):
        logger.debug(f"Starting process_state_updates thread, thread_id: {threading.current_thread().ident}")
        while True:
            try:
                (camera_id, task_path_id), state = self.queue_manager_queue.get(timeout=1)
                logger.debug(f"Received from queue_manager_queue (id: {id(self.queue_manager_queue)}): {(camera_id, task_path_id)} -> {state}")

                task_id = task_path_id.split('_')[1]
                task_type = task_path_id.split('_')[0]

                prev_state = self.prev_states.get((camera_id, task_path_id), None)
                if prev_state == state:
                    logger.debug(f"Skipping unchanged state: {(camera_id, task_path_id)} -> {state}")
                    continue

                self.prev_states[(camera_id, task_path_id)] = state

                if task_type == "starts" and task_id in START_TASK_PATHS:
                    if state:
                        if (task_id) not in self.start_queue:
                            self.start_queue.append((task_id))
                            logger.debug(f"Added to start_queue: {(task_id)}")
                    else:
                        if (task_id) in self.start_queue:
                            self.start_queue.remove((task_id))
                            logger.debug(f"Removed from start_queue: {(task_id)}")

                if task_type == "ends" and task_id in END_TASK_PATHS:
                    if not state:
                        if (task_id) not in self.end_queue:
                            self.end_queue.append((task_id))
                            logger.debug(f"Added to end_queue: {(task_id)}")
                    else:
                        if (task_id) in self.end_queue:
                            self.end_queue.remove((task_id))
                            logger.debug(f"Removed from end_queue: {(task_id)}")

                self.pair_monitor_queue.put({"start_queue": list(self.start_queue), "end_queue": list(self.end_queue)})
                logger.debug(f"Sent to pair_monitor_queue: {{'start_queue': {list(self.start_queue)}, 'end_queue': {list(self.end_queue)}}}")
                
            except queue.Empty:
                logger.debug("queue_manager_queue is empty, waiting for updates")
                continue
            except Exception as e:
                logger.error(f"Error processing state update: {e}")