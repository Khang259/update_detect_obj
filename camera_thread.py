import cv2
import threading
from utils import detect_lines, draw_lines_and_text

class CameraThread(threading.Thread):
    def __init__(self, camera_id, url, bounding_boxes, state_manager):
        super().__init__()
        self.camera_id = camera_id
        self.url = url
        self.bounding_boxes = bounding_boxes
        self.state_manager = state_manager
        self.cap = cv2.VideoCapture(url)
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print(f"Camera {self.camera_id} failed to read frame")
                break

            # Xử lý từng loại task_path
            for task_type in ["starts", "ends"]:
                for idx, bbox in enumerate(self.bounding_boxes[task_type]):
                    x1, y1, x2, y2 = bbox
                    roi = frame[y1:y2, x1:x2]
                    has_lines = detect_lines(roi)
                    state = has_lines if task_type == "starts" else not has_lines
                    task_path_id = f"{task_type}_{idx}"
                    self.state_manager.update_state(self.camera_id, task_path_id, state)
                    
                    # Vẽ bounding box và ghi chú lên frame
                    draw_lines_and_text(frame, bbox, has_lines)

            # Hiển thị frame (tùy chọn)
            cv2.imshow(f"Camera {self.camera_id}", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False

        self.cap.release()
        cv2.destroyWindow(f"Camera {self.camera_id}")