import cv2

# Đường dẫn đến file MP4
video_path = '20250612_20250612222049_20250613010114_222051.mp4'  # Đổi tên file nếu cần

# Mở video
cap = cv2.VideoCapture(video_path)

# Kiểm tra nếu mở không thành công
if not cap.isOpened():
    print("Không thể mở file video.")
    exit()

# Đọc và hiển thị từng frame
while True:
    ret, frame = cap.read()
    
    if not ret:
        print("Đã hết video hoặc lỗi đọc file.")
        break

    cv2.imshow("Video", frame)

    # Nhấn 'q' để thoát
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()
