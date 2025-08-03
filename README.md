#Mô tả dự án
Hệ thống sử dụng camera IP (RTSP) để giám sát khu vực cấp/trả hàng, 
tự động phát hiện hàng hóa bằng thuật toán Hough Transform, 
và gửi yêu cầu POST đến hệ thống điều phối khi phát hiện điều kiện hợp lệ.

project/
├── main.py              # Tệp chính để khởi chạy chương trình
├── camera_thread.py     # Xử lý luồng RTSP và phát hiện hàng bằng Hough Transform
├── state_manager.py     # Quản lý trạng thái của các task_path
├── pair_manager.py      # Quản lý các cặp (locked_pair) và logic kiểm tra
├── post_request.py      # Gửi yêu cầu POST trong luồng riêng
├── config.py            # Cấu hình camera, bounding box, cặp start-end
└── utils.py             # Hàm tiện ích, như phát hiện đường thẳng bằng Hough Transform

#Maintain-Upgrade
+-------------------+
|      main.py      |
|                   |
| 1. Init StateMgr  |----> [StateManager]
| 2. Start Camera   |----> [CameraThread 1] ----> [CameraThread N]
| 3. Start PairMgr  |----> [PairManager]
+-------------------+

[CameraThread]
  | 1. Read frame from RTSP (cv2.VideoCapture)
  | 2. For each bounding box (config.BOUNDING_BOXES):
  |    - Extract ROI
  |    - Call utils.detect_lines(ROI) ----> [utils.py]
  |    - Update state in StateManager ----> [StateManager]
  |    - Draw on frame (utils.draw_lines_and_text) ----> [utils.py]
  | 3. Display frame (cv2.imshow)

[StateManager]
  | - Thread-safe state dict (camera_id, task_path_id) -> state
  | - update_state(camera_id, task_path_id, state)
  | - get_state(camera_id, task_path_id) -> state

[PairManager]
  | 1. Monitor pairs (config.PAIRS)
  | 2. For each pair (camera_id, start_idx, end_idx):
  |    - Get states from StateManager ----> [StateManager]
  |    - If start=True, end=False for 10s:
  |       - Call post_request.delay_post_request ----> [post_request.py]
  |    - Update pair_states (post_sent, timer)

[post_request.py]
  | - delay_post_request: Recheck states, then call send_post_request
  | - send_post_request: Send POST to config.API_URL with pair data

[utils.py]
  | - detect_lines: Hough Transform to detect lines in ROI
  | - draw_lines_and_text: Draw bounding box and label on frame

[config.py]
  | - CAMERA_URLS: List of RTSP URLs
  | - BOUNDING_BOXES: List of start/end bounding boxes per camera
  | - PAIRS: List of (start_idx, end_idx) per camera
  | - API_URL: Endpoint for POST requests
