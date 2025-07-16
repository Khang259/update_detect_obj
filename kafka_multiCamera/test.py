# test.py
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='192.168.1.99:9092',  # ← sửa đúng IP đã đặt ở Kafka
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
