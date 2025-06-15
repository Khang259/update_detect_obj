# state_manager.py
import threading
import logging
from datetime import datetime
import os

# Logging configuration
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
    def __init__(self):
        """Initialize thread-safe state manager."""
        self.states = {}  # (camera_id, task_path_id) -> state
        self.lock = threading.Lock()
        logger.info("StateManager initialized")

    def update_state(self, camera_id: int, task_path_id: str, state: bool) -> None:
        """Update state for a camera and task path."""
        try:
            with self.lock:
                self.states[(camera_id, task_path_id)] = state
                logger.info(f"Updated state for camera {camera_id}, task_path {task_path_id}: {state}")
        except Exception as e:
            logger.error(f"Error updating state for camera {camera_id}, task_path {task_path_id}: {e}")
            raise

    def batch_update(self, updates: dict):
        logger.debug(f"Batch updating states: {updates}")
        try:
            with self.lock:
                for key, value in updates.items():
                    self.states[key] = value
                logger.info(f"Batch updated states for camera {updates.keys()}")
        except Exception as e:
            logger.error(f"Error in batch_update: {e}", exc_info=True)
            raise

    def get_state(self, camera_id: int, task_path_id: str) -> bool:
        logger.debug(f"Retrieving state for camera {camera_id}, task_path {task_path_id}")
        try:
            with self.lock:
                state = self.states.get((camera_id, task_path_id), False)
                logger.debug(f"Retrieved state: {state}")
                return state
        except Exception as e:
            logger.error(f"Error in get_state: {e}", exc_info=True)
            raise