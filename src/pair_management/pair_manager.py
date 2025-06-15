import threading
from src.pair_management.logging_config import setup_logging
from src.pair_management.pair_state import PairStateManager
from src.pair_management.pair_rotate import PairRotateManager
from src.pair_management.pair_monitor import PairMonitor
from src.pair_management.pair_post import PairPostManager
from src.pair_management.pair_lock import PairLockManager

class PairManager:
    def __init__(self, available_pairs, state_manager, api_url):
        self.logger = setup_logging()
        self.locks = [threading.Lock() for _ in range(len(available_pairs))]
        self.lock_manager_lock = threading.Lock()  # Lock riêng cho PairLockManager
        self.rotate_manager_lock = threading.Lock()  # Lock riêng cho PairRotateManager
        self.end_task_camera_map = {
            "10000164": 0, "10000170": 2, "10000171": 2, "10000140": 2,
            "10000141": 2, "10000147": 1,
            "10000125": 3, "10000126": 3
        }
        self.pair_state_manager = PairStateManager(available_pairs, state_manager, self.end_task_camera_map)
        self.pair_lock_manager = PairLockManager(self.pair_state_manager, self.lock_manager_lock)
        self.pair_rotate_manager = PairRotateManager(self.pair_state_manager, self.rotate_manager_lock)
        self.pair_post_manager = PairPostManager(self, api_url)
        self.pair_monitor = PairMonitor(self, self.pair_state_manager, self.pair_rotate_manager, self.pair_lock_manager, self.pair_post_manager)
        self.logger.info("PairManager initialized")

    def start_monitoring(self):
        monitor_thread = threading.Thread(target=self.pair_monitor.monitor_pairs, daemon=True, name="PairMonitorThread")
        monitor_thread.start()
        self.logger.info(f"Started pair monitoring thread: {monitor_thread.name}, alive={monitor_thread.is_alive()}")
        return monitor_thread

    def stop_monitoring(self):
        self.pair_monitor.running = False
        self.logger.info("Stopped pair monitoring")