import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from src.camera_thread.camera_thread import CameraThread

logger = logging.getLogger("camera_thread")

class CameraManager:
    def __init__(self, state_manager, max_workers=3):
        self.state_manager = state_manager
        self.cameras = {}  # camera_id -> CameraThread
        self.executor = ThreadPoolExecutor(max_workers=max_workers)  # 200 workers for 200 cameras
        self.shutdown_event = threading.Event()
        logger.debug("CameraManager initialized")

    def add_camera(self, camera_id, url, bounding_boxes):
        """Thêm camera mới"""
        if camera_id in self.cameras:
            logger.warning(f"Camera {camera_id} already exists")
            return False
        try:
            camera = CameraThread(camera_id, url, bounding_boxes, self.state_manager, self.shutdown_event)
            self.cameras[camera_id] = camera
            self.executor.submit(camera.run)
            logger.info(f"Added camera {camera_id} with URL {url}")
            return True
        except Exception as e:
            logger.error(f"Error adding camera {camera_id}: {e}", exc_info=True)
            return False

    def remove_camera(self, camera_id):
        """Xóa camera"""
        if camera_id not in self.cameras:
            logger.warning(f"Camera {camera_id} not found")
            return False
        try:
            camera = self.cameras.pop(camera_id)
            camera.running = False
            logger.info(f"Removed camera {camera_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}", exc_info=True)
            return False

    def stop_all(self):
        """Dừng tất cả camera"""
        self.shutdown_event.set()
        for camera in self.cameras.values():
            camera.running = False
        self.executor.shutdown(wait=True)
        self.cameras.clear()
        logger.info("All cameras stopped")