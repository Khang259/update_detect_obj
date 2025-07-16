# consumer_ai_hough.py
import base64
import cv2
import numpy as np
import json
from kafka import KafkaConsumer

# 1. Kết nối Kafka
consumer = KafkaConsumer(
    'camera_frames',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='ai_workers'
)

# 2. Hàm xử lý Hough Transform
def detect_lines_with_hough(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50, minLineLength=55, maxLineGap=10)
    
    output = img.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
    return output

# 3. Nhận và xử lý frame
received_cameras = set()
EXPECTED_NUM_CAMERAS = 10

for message in consumer:
    data = message.value
    print(data)
    camera_id = data['camera_id']
    received_cameras.add(camera_id)
    print(f"Cameras đã nhận: {sorted(received_cameras)} ({len(received_cameras)}/{EXPECTED_NUM_CAMERAS})")
    if len(received_cameras) == EXPECTED_NUM_CAMERAS:
        print("ĐÃ NHẬN ĐỦ 10 CAMERA TỪ PRODUCER!")
    img_data = base64.b64decode(data['frame'])
    np_arr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    processed_img = detect_lines_with_hough(img)
    print(f"[{camera_id}] Processed frame with HoughLines")

    # Hiển thị kết quả
    cv2.imshow(f'Hough - {camera_id}', processed_img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
