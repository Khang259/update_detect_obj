import logging
import threading
import signal
import os
import time
from datetime import datetime
from src.state_manager.state_manager import StateManager
from src.camera_thread.camera_manager import CameraManager
from src.config.camera_config import CameraConfig
from src.pair_management.pair_manager import PairManager
from src.pair_management.queue_manager import QueueManager
from src.config.config import API_URL, BBOX_TO_TASKPATH, validate_config
from src.pair_management.logging_config import setup_logging  # Thêm import

# Setup logging for pair_manager
logger = setup_logging()  # Gọi setup_logging()

# Logging configuration for main
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
    camera_manager = None
    pair_manager = None

    def handle_shutdown(signum=None, frame=None):
        main_logger.info(f"Shutdown triggered (signal: {signum if signum else 'manual'})")
        shutdown_event.set()
        if camera_manager:
            camera_manager.stop_all()
        if pair_manager:
            pair_manager.stop_monitoring()
        main_logger.info("Program terminated successfully")
        if signum:
            os._exit(0)

    try:
        state_manager = StateManager()
        camera_config = CameraConfig()
        camera_manager = CameraManager(state_manager, max_workers=3)

        queue_manager = QueueManager()

        available_pairs = []
        end_task_camera_map = {}
        camera_urls = [
            "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101",
            "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101",
            "rtsp://admin:Soncave1!@192.168.1.29:554/streaming/channels/101"
        ]
        bounding_boxes = [
            {
                "starts": [
                    [827, 524, 943, 641], [655, 522, 785, 630], [514, 503, 615, 642],
                    [368, 487, 445, 610], [238, 477, 283, 599], [126, 481, 153, 634],
                    [4, 442, 50, 610]
                ],
                "ends": [[991, 532, 1079, 623]]
            },
            {
                "starts": [[925, 391, 958, 486], [801, 571, 911, 697]],
                "ends": [[573, 259, 651, 307]]
            },
            {
                "starts": [[444, 384, 518, 485]],
                "ends": [[862, 385, 948, 494], [643, 387, 740, 495], [871, 167, 947, 287], [655, 170, 739, 280]]
            }
        ]
        for camera_id in range(3):
            config = camera_config.get_camera(camera_id)
            if not config:
                url = camera_urls[camera_id]
                bboxes = bounding_boxes[camera_id]
                camera_config.add_camera(camera_id, url, bboxes)
                config = camera_config.get_camera(camera_id)
            camera_manager.add_camera(camera_id, config["url"], config["bounding_boxes"])
            available_pairs.append({
                "starts": [BBOX_TO_TASKPATH[f"{x[0]}_{x[1]}_{x[2]}_{x[3]}"] for x in config["bounding_boxes"]["starts"]],
                "ends": [BBOX_TO_TASKPATH[f"{x[0]}_{x[1]}_{x[2]}_{x[3]}"] for x in config["bounding_boxes"]["ends"]]
            })
            for end_bbox in config["bounding_boxes"]["ends"]:
                end_idx = BBOX_TO_TASKPATH[f"{end_bbox[0]}_{end_bbox[1]}_{end_bbox[2]}_{end_bbox[3]}"]
                end_task_camera_map[end_idx] = camera_id

        validate_config(available_pairs)

        pair_manager = PairManager(
            available_pairs=available_pairs,
            state_manager=state_manager,
            api_url=API_URL,
            end_task_camera_map=end_task_camera_map,
            queue_manager=queue_manager
        )

        pair_manager.start_monitoring()

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