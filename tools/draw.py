import cv2
import numpy as np

# Biến toàn cục để lưu tọa độ bounding box
drawing = False  # Trạng thái vẽ
start_point = (-1, -1)  # Điểm bắt đầu
end_point = (-1, -1)  # Điểm kết thúc
boxes = []  # Danh sách lưu các bounding box

# Hàm xử lý sự kiện chuột
def draw_bounding_box(event, x, y, flags, param):
    global drawing, start_point, end_point, boxes

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_point = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_point = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_point = (x, y)
        boxes.append((start_point, end_point))
        # In tọa độ bounding box lên terminal
        print(f"Bounding Box: Start Point = {start_point}, End Point = {end_point}")

def main(rtsp_url):
    # Mở stream RTSP
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("Không thể mở stream RTSP. Kiểm tra URL hoặc kết nối.")
        return

    # Tạo cửa sổ và gán hàm xử lý chuột
    cv2.namedWindow("RTSP Stream")
    cv2.setMouseCallback("RTSP Stream", draw_bounding_box)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể nhận frame. Thoát...")
            break

        # Tạo một bản sao của frame để vẽ
        frame_copy = frame.copy()

        # Vẽ tất cả các bounding box đã lưu
        for i, (start, end) in enumerate(boxes):
            # Đảm bảo tọa độ hợp lệ
            x1, y1 = start
            x2, y2 = end
            top_left = (min(x1, x2), min(y1, y2))
            bottom_right = (max(x1, x2), max(y1, y2))
            # Vẽ bounding box với màu ngẫu nhiên
            color = (0, 255, 0)
            cv2.rectangle(frame_copy, top_left, bottom_right, color, 2)
            # Hiển thị tọa độ trên frame
            cv2.putText(frame_copy, f"Box {i+1}: {top_left}, {bottom_right}", 
                       (top_left[0], top_left[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Vẽ bounding box đang được kéo
        if drawing and start_point != (-1, -1) and end_point != (-1, -1):
            cv2.rectangle(frame_copy, start_point, end_point, (0, 255, 0), 2)

        # Hiển thị frame
        cv2.imshow("RTSP Stream", frame_copy)

        # Thoát khi nhấn 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Thay thế bằng URL RTSP của bạn
    rtsp_url = "rtsp://admin:Soncave1!@192.168.1.27:554/streaming/channels/101"
    main(rtsp_url)