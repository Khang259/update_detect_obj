import logging
from queue import Queue
import threading
from time import time

logger = logging.getLogger("pair_manager")

class QueueManager:
    def __init__(self):
        self.end_queue = Queue()
        self.lock = threading.Lock()
        self.last_refresh = {}  # camera_id -> timestamp
        self.seen_end_idx = set()  # Tránh trùng lặp
        logger.debug("QueueManager initialized")

    def add_end_idx(self, camera_id, end_idx):
        """Thêm end_idx vào queue, tránh trùng lặp"""
        with self.lock:
            key = (camera_id, end_idx)
            if key not in self.seen_end_idx:
                self.end_queue.put(key)
                self.seen_end_idx.add(key)
                logger.debug(f"Added to queue: {key}")
            else:
                logger.debug(f"Skipped duplicate: {key}")

    def get_end_idx(self):
        """Lấy end_idx từ queue"""
        try:
            key = self.end_queue.get_nowait()
            with self.lock:
                self.seen_end_idx.discard(key)
            logger.debug(f"Retrieved from queue: {key}")
            return key
        except Queue.Empty:
            logger.debug("Queue empty")
            return None

    def refresh_queue(self, camera_id, valid_end_list):
        """Làm mới queue cho camera"""
        with self.lock:
            current_time = time()
            if camera_id not in self.last_refresh or current_time - self.last_refresh[camera_id] >= 60:
                for end_idx in valid_end_list:
                    key = (camera_id, end_idx)
                    if key not in self.seen_end_idx:
                        self.end_queue.put(key)
                        self.seen_end_idx.add(key)
                        logger.debug(f"Refreshed queue with: {key}")
                self.last_refresh[camera_id] = current_time
                logger.info(f"Queue refreshed for camera {camera_id}")