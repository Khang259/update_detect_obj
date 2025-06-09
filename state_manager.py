# state_manager.py
import threading
import logging
from datetime import datetime
import os

# Logging configuration
os.makedirs("logs", exist_ok=True)
log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
date_str = datetime.now().strftime("%Y%m%d")
log_handler = logging.FileHandler(f"logs/log_state_manager_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler("logs/log_error.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("state_manager")
logger.setLevel(logging.INFO)
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

    def batch_update(self, updates: dict) -> None:
        """Batch update states for multiple task paths."""
        try:
            with self.lock:
                self.states.update(updates)
                for (camera_id, task_path_id), state in updates.items():
                    logger.info(f"Updated state for camera {camera_id}, {task_path_id}: {state}")
                logger.info(f"Batch updated states for camera {updates.keys()}")
        except Exception as e:
            logger.error(f"Error in batch update: {e}")
            raise

    def get_state(self, camera_id: int, task_path_id: str) -> bool:
        """Get state for a camera and task path."""
        try:
            with self.lock:
                state = self.states.get((camera_id, task_path_id), False)
                logger.debug(f"Retrieved state for camera {camera_id}, task_path {task_path_id}: {state}")
                return state
        except Exception as e:
            logger.error(f"Error retrieving state for camera {camera_id}, task_path {task_path_id}: {e}")
            raise