
import cv2
import threading
import logging
from queue import Queue
import queue
from datetime import datetime
import os
import subprocess
import numpy as np

from src.utils.utils import detect_lines, draw_lines_and_text
from src.config.config import BBOX_TO_TASKPATH

date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_camera_thread", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_camera_thread", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_camera_thread/log_camera_thread_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_camera_thread/logs_errors_camera_thread_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("camera_thread")
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

class DisplayThread(threading.Thread):
    def __init__(self, camera_id: int, frame_queue: Queue, shutdown_event: threading.Event):
        super().__init__()
        self.camera_id = camera_id
        self.frame_queue = frame_queue
        self.shutdown_event = shutdown_event
        self.running = True
        self.window_created = False
        logger.info(f"DisplayThread for camera {camera_id} initialized")

    def run(self):
        while self.running and not self.shutdown_event.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
                cv2.imshow(f"Camera {self.camera_id}", frame)
                self.window_created = True
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info(f"Quit key 'q' detected for camera {self.camera_id}")
                    self.shutdown_event.set()
                    self.running = False
                    break
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error displaying frame for camera {self.camera_id}: {e}")
                continue

        if self.window_created:
            try:
                cv2.destroyWindow(f"Camera {self.camera_id}")
                cv2.waitKey(1)
                logger.info(f"Display window for camera {self.camera_id} closed")
            except Exception as e:
                logger.error(f"Error closing display window for camera {self.camera_id}: {e}")
        else:
            logger.info(f"No display window was created for camera {self.camera_id}")

class CameraThread(threading.Thread):
    def __init__(self, camera_id: int, url: str, bounding_boxes: dict, state_queue: Queue, shutdown_event: threading.Event, width=1280, height=720):
        super().__init__()
        self.camera_id = camera_id
        self.url = url
        self.bounding_boxes = bounding_boxes
        self.state_queue = state_queue
        self.shutdown_event = shutdown_event
        self.running = True
        self.frame_queue = Queue(maxsize=10)
        self.display_thread = DisplayThread(camera_id, self.frame_queue, shutdown_event)
        self.display_thread.start()
        self.width = width
        self.height = height
        logger.info(f"CameraThread for camera {camera_id} initialized with URL {url}")

    def run(self):
        command = [
            "ffmpeg",
            "-rtsp_transport", "tcp",
            "-i", self.url,
            "-loglevel", "quiet",
            "-an",
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-"
        ]

        process = subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=10**8)
        frame_size = self.width * self.height * 3

        while self.running and not self.shutdown_event.is_set():
            raw_frame = process.stdout.read(frame_size)
            if len(raw_frame) != frame_size:
                logger.error(f"Camera {self.camera_id} received incomplete frame")
                continue

            frame = np.frombuffer(raw_frame, dtype=np.uint8).reshape((self.height, self.width, 3))
            frame = frame.copy()

            updates = {}
            for task_type in ["starts", "ends"]:
                for bbox in self.bounding_boxes[task_type]:
                    x1, y1, x2, y2 = bbox
                    try:
                        roi = frame[y1:y2, x1:x2]
                        has_lines = detect_lines(roi)
                        state = has_lines
                        bbox_key = f"{x1}_{y1}_{x2}_{y2}"
                        task_path_id = f"{task_type}_{BBOX_TO_TASKPATH[bbox_key]}"
                        updates[(self.camera_id, task_path_id)] = state
                        draw_lines_and_text(frame, bbox, has_lines)
                    except Exception as e:
                        logger.error(f"Error processing bbox {bbox} for camera {self.camera_id}: {e}")
                        continue

            try:
                self.state_queue.put(updates)
                logger.debug(f"Sent updates for camera {self.camera_id}: {updates}")
            except Exception as e:
                logger.error(f"Error sending updates for camera {self.camera_id}: {e}")

            if not self.frame_queue.full():
                self.frame_queue.put(frame)
            else:
                logger.warning(f"Frame queue full for camera {self.camera_id}, frame dropped")
            
        process.terminate()
        self.display_thread.running = False
        self.display_thread.join(timeout=2.0)
        logger.info(f"CameraThread for camera {self.camera_id} stopped")
