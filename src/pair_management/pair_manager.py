import logging
import threading
from queue import Queue
from src.state_manager.state_manager import StateManager
from src.pair_management.pair_monitor import PairMonitor
from src.post_request.post_request import PostRequestManager
from src.pair_management.queue_manager import QueueManager

logger = logging.getLogger("pair_manager")

class PairManager:
    def __init__(self, available_pairs, api_url, state_queue: Queue):
        self.state_queue = state_queue
        self.queue_manager_queue = Queue()
        self.pair_monitor_queue = Queue()
        self.sent_pairs_queue = Queue()
        self.state_manager = StateManager(self.state_queue, self.queue_manager_queue)
        self.queue_manager = QueueManager(self.queue_manager_queue, self.pair_monitor_queue)
        self.post_request_manager = PostRequestManager(api_url, self.sent_pairs_queue)
        self.pair_monitor = PairMonitor(self.state_manager, self.post_request_manager, self.pair_monitor_queue, self.sent_pairs_queue)
        self.state_thread = threading.Thread(target=self.state_manager.process_updates)
        self.queue_thread = threading.Thread(target=self.queue_manager.process_state_updates)  # Khởi tạo queue_thread
        logger.debug(f"PairManager initialized with state_queue id: {id(self.state_queue)}")

    def start_monitoring(self):
        logger.info("Starting state_thread")
        self.state_thread.start()
        logger.info("Starting queue_thread")
        self.queue_thread.start()
        logger.info("Starting post_request_manager")
        self.post_request_manager.start()
        logger.info("Starting pair_monitor")
        self.pair_monitor.start_monitoring()
        logger.info("Started monitoring")

    def stop_monitoring(self):
        logger.info("Stopping pair_monitor")
        self.pair_monitor.stop_monitoring()
        logger.info("Stopping post_request_manager")
        self.post_request_manager.stop()
        logger.info("Stopping state_manager")
        self.state_manager.stop()
        logger.info("Stopping queue_thread")
        if self.queue_thread.is_alive():
            self.queue_thread.join(timeout=2.0)
        logger.info("Stopping state_thread")
        if self.state_thread.is_alive():
            self.state_thread.join(timeout=2.0)
        logger.info("Monitoring stopped")