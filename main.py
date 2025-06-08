import threading
import signal
from camera_thread import CameraThread
from state_manager import StateManager
from pair_manager import PairManager
from config import CAMERA_URLS, BOUNDING_BOXES, PAIRS, API_URL

def main():
    #Track the state of bounding boxes (start/end points)
    state_manager = StateManager()

    # Khởi động các luồng camera
    camera_threads = []
    for i, url in enumerate(CAMERA_URLS):
        thread = CameraThread(i, url, BOUNDING_BOXES[i], state_manager)
        thread.start()
        camera_threads.append(thread)

    # Khởi động quản lý cặp
    pair_manager = PairManager(PAIRS, state_manager, API_URL)
    pair_thread = threading.Thread(target=pair_manager.monitor_pairs)
    pair_thread.start()

    # Chờ các luồng camera (có thể thêm cơ chế dừng chương trình)
    for thread in camera_threads:
        thread.join()
    pair_thread.join()

if __name__ == "__main__":
    main()