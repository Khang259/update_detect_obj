import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import platform

# Danh sách 10 IP camera
CAMERA_IPS = [
    "192.168.1.26",
    "192.168.1.6",
    "192.168.1.7",
    "192.168.1.104",
    "192.168.1.105",
    "192.168.1.106",
    "192.168.1.107",
    "192.168.1.108",
    "192.168.1.109",
    "192.168.1.110"
]

# Hàm kiểm tra thiết bị online bằng ping
def is_online(ip: str) -> bool:
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", ip]
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return result.returncode == 0
    except:
        return False

# Hàm cập nhật trạng thái cho từng IP
def update_status(index, label):
    ip = CAMERA_IPS[index]
    online = is_online(ip)
    status_text = "🟢 Online" if online else "🔴 Offline"
    label.config(text=f"{ip} - {status_text}", foreground="green" if online else "red")

# Hàm cập nhật toàn bộ danh sách
def refresh_status():
    for i, label in enumerate(status_labels):
        threading.Thread(target=update_status, args=(i, label), daemon=True).start()

# Tạo giao diện
root = tk.Tk()
root.title("Camera Connection Monitor")
root.geometry("400x400")

tk.Label(root, text="Camera Status Checker", font=("Arial", 16, "bold")).pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=10)

status_labels = []
for ip in CAMERA_IPS:
    lbl = tk.Label(frame, text=f"{ip} - Checking...", font=("Arial", 12))
    lbl.pack(anchor="w", pady=2)
    status_labels.append(lbl)

btn_refresh = tk.Button(root, text="🔄 Refresh", command=refresh_status, font=("Arial", 12))
btn_refresh.pack(pady=10)

# Lần đầu khởi chạy tự động kiểm tra
refresh_status()

root.mainloop()
