# Đường dẫn RTSP của các camera
CAMERA_URLS = [
    # "rtsp://admin:admin@192.168.1.67:1935"
    "rtsp://localhost:8554/stream"
]

# Bounding box cho mỗi camera: (x1, y1, x2, y2)
BOUNDING_BOXES = {
    0: {
        "starts": [(100, 100, 200, 200), (300, 100, 400, 200)],  # Hai start_task_path
        "ends": [(100, 300, 200, 400), (300, 300, 400, 400)]     # Hai end_task_path
    },
    1: {
        "starts": [(150, 150, 250, 250)],
        "ends": [(150, 350, 250, 450)]
    }
}

# Các cặp start-end được định nghĩa trước: (start_idx, end_idx)
PAIRS = {
    0: [(0, 0), (1, 1)],  # Camera 0: start0-end0, start1-end1
    1: [(0, 0)]           # Camera 1: start0-end0
}

# URL API để gửi POST request
API_URL = "http://192.168.1.50:8000/ics/taskOrder/addTask"