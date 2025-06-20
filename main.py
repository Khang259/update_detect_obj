import logging
import threading
import signal
import os
import time
from datetime import datetime
from queue import Queue
from src.camera_thread.camera_thread import CameraThread
from src.pair_management.pair_manager import PairManager
from src.config.config import CAMERA_URLS, BOUNDING_BOXES, API_URL, validate_config, BBOX_TO_TASKPATH

date_str = datetime.now().strftime("%Y%m%d")
os.makedirs("logs/logs_main", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_main", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_main/log_main_{date_str}.log")
log_handler.setFormatter(log_formatter)
error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_main/logs_errors_main_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)
main_logger.addHandler(log_handler)
main_logger.addHandler(error_handler)

def main():
    main_logger.info("Starting main program")
    shutdown_event = threading.Event()
    cameras = []
    pair_manager = None

    def handle_shutdown(signum=None, frame=None):
        main_logger.info(f"Shutdown triggered (signal: {signum if signum else 'manual'})")
        shutdown_event.set()
        for camera in cameras:
            camera.running = False
            camera.join(timeout=2.0)
        if pair_manager:
            pair_manager.stop_monitoring()
        main_logger.info("Program terminated successfully")
        if signum:
            os._exit(0)

    try:
        state_queue = Queue()
        main_logger.info(f"Created state_queue with id: {id(state_queue)}")
        available_pairs = [
            {
                "starts": [BBOX_TO_TASKPATH[f"{x[0]}_{x[1]}_{x[2]}_{x[3]}"] for x in bboxes["starts"]],
                "ends": [BBOX_TO_TASKPATH[f"{x[0]}_{x[1]}_{x[2]}_{x[3]}"] for x in bboxes["ends"]]
            } for bboxes in BOUNDING_BOXES
        ]
        validate_config(available_pairs)

        pair_manager = PairManager(available_pairs, API_URL, state_queue)  # Truyền state_queue
        pair_manager.start_monitoring()

        for camera_id, (url, bboxes) in enumerate(zip(CAMERA_URLS, BOUNDING_BOXES)):
            main_logger.info(f"Starting CameraThread {camera_id} with state_queue id: {id(state_queue)}")
            camera = CameraThread(camera_id, url, bboxes, state_queue, shutdown_event)
            cameras.append(camera)
            camera.start()

        signal.signal(signal.SIGINT, handle_shutdown)
        signal.signal(signal.SIGTERM, handle_shutdown)

        while not shutdown_event.is_set():
            shutdown_event.wait(1.0)

    except Exception as e:
        main_logger.error(f"Error in main: {e}", exc_info=True)
        handle_shutdown()
        raise

if __name__ == "__main__":
    main()