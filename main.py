import threading
import logging
from datetime import datetime
import os
import signal
import cv2
from src.camera_thread.camera_thread import CameraThread
from src.state_manager.state_manager import StateManager
from src.pair_management.pair_manager import PairManager
from src.config import CAMERA_URLS, BOUNDING_BOXES, AVAILABLE_PAIRS, API_URL

# Logging configuration
date_str = datetime.now().strftime("%Y%m%d")

os.makedirs("logs/logs_main", exist_ok=True)
os.makedirs("logs/logs_errors/logs_errors_main", exist_ok=True)

log_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_handler = logging.FileHandler(f"logs/logs_main/log_main_{date_str}.log")
log_handler.setFormatter(log_formatter)

error_handler = logging.FileHandler(f"logs/logs_errors/logs_errors_main/logs_errors_main_{date_str}.log")
error_handler.setFormatter(log_formatter)
error_handler.setLevel(logging.ERROR)

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(error_handler)

def main():
    logger.info("Starting main program")
    state_manager = StateManager()
    camera_threads = []
    pair_manager = None
    pair_thread = None
    shutdown_event = threading.Event()  # Event to signal shutdown

    def handle_shutdown(signum=None, frame=None, threads=None, manager=None):
        logger.info(f"Shutdown triggered (signal: {signum if signum else 'manual'})")
        shutdown_event.set()  # Signal all threads to stop
        for thread in threads or []:
            thread.running = False
            logger.info(f"Stopping CameraThread for camera {thread.camera_id}")
            thread.join(timeout=2.0)
        if manager:
            manager.running = False
            logger.info("Stopping PairManager")
            if pair_thread:
                pair_thread.join(timeout=2.0)
        cv2.destroyAllWindows()  # Close all OpenCV windows
        logger.info("All OpenCV windows closed")
        logger.info("Program terminated successfully")
        if signum:
            os._exit(0)  # Force exit on signal

    try:
        # Start camera threads
        for i, url in enumerate(CAMERA_URLS):
            thread = CameraThread(i, url, BOUNDING_BOXES[i], state_manager, shutdown_event)
            thread.start()
            camera_threads.append(thread)
            logger.info(f"Started CameraThread for camera {i}")

        # Start pair manager
        pair_manager = PairManager(AVAILABLE_PAIRS, state_manager, API_URL)
        pair_thread = threading.Thread(target=pair_manager.pair_monitor.monitor_pairs)
        pair_thread.start()
        logger.info("Started PairManager thread")

        # Register signal handlers
        signal.signal(signal.SIGINT, lambda s, f: handle_shutdown(s, f, camera_threads, pair_manager))
        signal.signal(signal.SIGTERM, lambda s, f: handle_shutdown(s, f, camera_threads, pair_manager))

        # Wait for threads or shutdown event
        while not shutdown_event.is_set():
            for thread in camera_threads:
                if not thread.is_alive():
                    logger.error(f"CameraThread for camera {thread.camera_id} stopped unexpectedly")
                    handle_shutdown(threads=camera_threads, manager=pair_manager)
                    break
            if pair_thread and not pair_thread.is_alive():
                logger.error("PairManager thread stopped unexpectedly")
                handle_shutdown(threads=camera_threads, manager=pair_manager)
                break
            shutdown_event.wait(1.0)

        # Wait for threads to complete after shutdown
        for thread in camera_threads:
            thread.join(timeout=2.0)
        if pair_thread:
            pair_thread.join(timeout=2.0)
        logger.info("All threads completed")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        handle_shutdown(threads=camera_threads, manager=pair_manager)
        raise
    finally:
        if not shutdown_event.is_set():
            handle_shutdown(threads=camera_threads, manager=pair_manager)

if __name__ == "__main__":
    main()