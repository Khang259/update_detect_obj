import logging
from datetime import datetime
import os
from queue import Queue
import queue
import threading

date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_state_manager", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_state_manager", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_state_manager/log_state_manager_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_state_manager/logs_errors_state_manager_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("state_manager")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class StateManager:
    def __init__(self, state_queue: Queue, queue_manager_queue: Queue):
        self.states = {}
        self.state_queue = state_queue
        self.queue_manager_queue = queue_manager_queue
        self.running = True
        logger.info(f"StateManager initialized with state_queue id: {id(self.state_queue)}")

    def process_updates(self):
        logger.debug(f"Starting process_updates thread, thread_id: {threading.current_thread().ident}")
        processed_keys = set()
        while self.running:
            try:
                updates = self.state_queue.get(timeout=1)
                logger.debug(f"Received updates from state_queue (id: {id(self.state_queue)}): {updates}")
                logger.debug(f"state_queue size after get: {self.state_queue.qsize()}")
                
                for key, value in updates.items():
                    prev_state = self.states.get(key, None)
                    self.states[key] = value
                    logger.debug(f"Updated state for {key}: {value} (previous: {prev_state})")
                    
                    if key not in processed_keys:
                        self.queue_manager_queue.put((key, value))
                        processed_keys.add(key)
                        logger.debug(f"Sent state to queue_manager_queue: {key} -> {value}")
                
                logger.info(f"Processed batch updates for {updates.keys()}")
                processed_keys.clear()
                
            except queue.Empty:
                logger.debug("state_queue is empty, waiting for updates")
                continue
            except Exception as e:
                logger.error(f"Error processing updates: {e}")

    def stop(self):
        self.running = False
        logger.info("StateManager stopped")