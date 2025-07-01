# rcs_server.py
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc chỉ định cụ thể, ví dụ ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ics/taskOrder/addTask")
async def receive_data(request: Request):
    payload =await request.json()
    print("Received:", payload)
    return {
        "code": 1000,
        "message": "Success"
    }

if __name__ == "__main__":
    # Lấy IP nội bộ của máy host

    # Chạy server trực tiếp
    uvicorn.run("server:app", host="192.168.0.108", port=7000, reload=True)
