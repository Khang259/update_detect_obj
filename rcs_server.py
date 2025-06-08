# rcs_server.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import socket

app = FastAPI()

# Định nghĩa schema nếu cần nhận JSON
class Payload(BaseModel):
    data: str

@app.post("/ics/taskOrder/addTask")
async def receive_data(payload: Payload):
    print("Received:", payload)
    return {
        "code": 1000,
        "message": "Success"
    }

if __name__ == "__main__":
    # Lấy IP nội bộ của máy host
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Chạy server trực tiếp
    uvicorn.run("rcs_server:app", host=local_ip, port=8000, reload=True)
