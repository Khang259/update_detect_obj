import logging
import threading
from src.pair_management.pair_state import PairStateManager
from src.pair_management.pair_rotate import PairRotateManager
from src.pair_management.pair_monitor import PairMonitor
from src.pair_management.pair_lock import PairLockManager
from src.pair_management.pair_post import PairPostManager

logger = logging.getLogger("pair_manager")

class PairManager:
    def __init__(self, available_pairs, state_manager, api_url, end_task_camera_map, queue_manager):
        self.locks = [threading.Lock() for _ in range(len(available_pairs))]
        self.pair_state_manager = PairStateManager(available_pairs, state_manager, end_task_camera_map)
        self.pair_rotate_manager = PairRotateManager(self.pair_state_manager, threading.Lock())
        self.pair_lock_manager = PairLockManager(self.pair_state_manager, threading.Lock())
        self.pair_post_manager = PairPostManager(self, api_url)
        self.pair_monitor = PairMonitor(
            self, self.pair_state_manager, self.pair_rotate_manager,
            self.pair_lock_manager, self.pair_post_manager, queue_manager
        )
        self.running = True
        logger.debug("PairManager initialized")

    def start_monitoring(self):
        logger.info("Starting monitoring")
        return self.pair_monitor.start_monitoring()

    def stop_monitoring(self):
        self.running = False
        self.pair_monitor.stop_monitoring()
        logger.info("Monitoring stopped")