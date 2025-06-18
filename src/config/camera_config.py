import json
import logging
import os

logger = logging.getLogger("camera_thread")

class CameraConfig:
    def __init__(self, config_file="camera_config.json"):
        self.config_file = config_file
        self.cameras = {}
        self.load_config()

    def load_config(self):
        """Tải cấu hình camera từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.cameras = json.load(f)
                logger.info(f"Loaded camera config from {self.config_file}")
            else:
                logger.warning(f"Config file {self.config_file} not found, using empty config")
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)

    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.cameras, f, indent=4)
            logger.info(f"Saved camera config to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config: {e}", exc_info=True)

    def add_camera(self, camera_id, url, bounding_boxes):
        """Thêm camera vào cấu hình"""
        self.cameras[str(camera_id)] = {
            "url": url,
            "bounding_boxes": bounding_boxes
        }
        self.save_config()

    def get_camera(self, camera_id):
        """Lấy thông tin camera"""
        return self.cameras.get(str(camera_id))

    def remove_camera(self, camera_id):
        """Xóa camera khỏi cấu hình"""
        if str(camera_id) in self.cameras:
            del self.cameras[str(camera_id)]
            self.save_config()