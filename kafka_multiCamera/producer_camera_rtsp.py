# producer_camera_rtsp.py
import cv2
import base64
import json
import threading
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def stream_camera(camera_idx):
    camera_id = f'cam_{camera_idx:02d}'
    rtsp_url = f'rtsp://localhost:8554/cam{camera_idx:02d}'
    cap = cv2.VideoCapture(rtsp_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        resized = cv2.resize(frame, (640, 480))
        _, buffer = cv2.imencode('.jpg', resized)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        message = {
            'camera_id': camera_id,
            'frame': jpg_as_text
        }
        producer.send('camera_frames', value=message)
        print(f"Frame sent from {camera_id}")
        cv2.waitKey(100)

# Tạo 10 thread cho 10 camera
threads = []
for i in range(1, 11):
    t = threading.Thread(target=stream_camera, args=(i,))
    t.start()
    threads.append(t)

# Giữ chương trình chạy
for t in threads:
    t.join()
