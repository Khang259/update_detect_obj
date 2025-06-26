import cv2
import numpy as np

class BoundingBoxDrawer:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.start_point = None
        self.end_point = None
        self.boxes = []
        
    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            self.start_point = (x, y)
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.end_point = (x, y)
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.end_point = (x, y)
            self.boxes.append((self.ix, self.iy, x, y))
            # In tọa độ ra terminal
            print(f"Bounding Box: Start({self.ix}, {self.iy}), End({x}, {y})")
            print(f"Width: {abs(x - self.ix)}, Height: {abs(y - self.iy)}")

    def run(self):
        # Kết nối RTSP stream
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print("Error: Cannot connect to RTSP stream")
            return

        # Tạo window và set mouse callback
        cv2.namedWindow('RTSP Stream')
        cv2.setMouseCallback('RTSP Stream', self.draw_rectangle)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            # Tạo một bản sao của frame để vẽ
            img = frame.copy()

            # Vẽ các bounding box đã lưu
            for box in self.boxes:
                cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

            # Vẽ line đang vẽ
            if self.drawing and self.start_point and self.end_point:
                cv2.rectangle(img, self.start_point, self.end_point, (0, 0, 255), 2)

            # Hiển thị frame
            cv2.imshow('RTSP Stream', img)

            # Thoát khi nhấn 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Giải phóng tài nguyên
        cap.release()
        cv2.destroyAllWindows()

def main():
    # Thay thế bằng RTSP URL của bạn
    # rtsp_url = "rtsp://admin:Soncave1!@192.168.1.28:554/streaming/channels/101"
    rtsp_url = "rtsp://admin:admin@192.168.0.115:1935"
    
    # Kiểm tra URL hợp lệ
    if not rtsp_url.startswith("rtsp://"):
        print("Error: Invalid RTSP URL")
        return

    drawer = BoundingBoxDrawer(rtsp_url)
    drawer.run()

if __name__ == "__main__":
    main()