import logging
import threading  # Thêm import threading
from queue import Queue, Empty
from collections import deque

logger = logging.getLogger("queue_manager")

class QueueManager:
    def __init__(self):
        self.end_queue = Queue()
        self.camera_queues = {}
        self.lock = threading.Lock()  # Sửa từ Queue() thành threading.Lock()
        logger.debug("QueueManager initialized")

    def add_end_idx(self, camera_id: int, end_idx: str):
        """Thêm end_idx vào hàng đợi toàn cục và camera queue"""
        try:
            with self.lock:
                if camera_id not in self.camera_queues:
                    self.camera_queues[camera_id] = deque()
                if end_idx not in self.camera_queues[camera_id]:
                    self.camera_queues[camera_id].append(end_idx)
                    self.end_queue.put((camera_id, end_idx))
                    logger.debug(f"Added to queue: ({camera_id}, {end_idx})")
        except Exception as e:
            logger.error(f"Error adding end_idx {end_idx} for camera {camera_id}: {e}")
            raise

    def get_end_idx(self):
        """Lấy end_idx từ hàng đợi toàn cục"""
        try:
            with self.lock:
                key = self.end_queue.get_nowait()
                logger.debug(f"Retrieved from queue: {key}")
                return key
        except Empty:
            logger.debug("Global queue is empty")
            return None
        except Exception as e:
            logger.error(f"Error getting end_idx: {e}")
            raise

    def refresh_queue(self, camera_id: int, valid_end_list: list):
        """Làm mới camera queue với valid_end_list"""
        try:
            with self.lock:
                if camera_id in self.camera_queues:
                    self.camera_queues[camera_id] = deque(valid_end_list)
                    logger.debug(f"Queue refreshed for camera {camera_id}: {list(self.camera_queues[camera_id])}")
                else:
                    self.camera_queues[camera_id] = deque(valid_end_list)
                    logger.debug(f"Queue initialized for camera {camera_id}: {list(self.camera_queues[camera_id])}")
        except Exception as e:
            logger.error(f"Error refreshing queue for camera {camera_id}: {e}")
            raise