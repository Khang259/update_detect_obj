import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import platform
import json
import os
import re
import cv2

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
            # Print coordinates to terminal
            print(f"Bounding Box: Start({self.ix}, {self.iy}), End({x}, {y})")
            print(f"Width: {abs(x - self.ix)}, Height: {abs(y - self.iy)}")

    def run(self):
        # Connect to RTSP stream
        cap = cv2.VideoCapture(self.rtsp_url)
        
        if not cap.isOpened():
            print("Error: Cannot connect to RTSP stream")
            return

        # Create window and set mouse callback
        cv2.namedWindow('RTSP Stream')
        cv2.setMouseCallback('RTSP Stream', self.draw_rectangle)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            # Create a copy of the frame to draw on
            img = frame.copy()

            # Draw saved bounding boxes
            for box in self.boxes:
                cv2.rectangle(img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

            # Draw the current rectangle being drawn
            if self.drawing and self.start_point and self.end_point:
                cv2.rectangle(img, self.start_point, self.end_point, (0, 0, 255), 2)

            # Display frame
            cv2.imshow('RTSP Stream', img)

            # Exit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Release resources
        cap.release()
        cv2.destroyAllWindows()

class ConfigRoiTab:
    def __init__(self, master):
        self.frame = tk.Frame(master)
        tk.Label(self.frame, text="Kiểm Tra Trạng Thái Camera", font=("Arial", 14, "bold")).pack(pady=20)

        # Frame for status labels
        self.status_frame = tk.Frame(self.frame)
        self.status_frame.pack(pady=10)

        # List to store status labels
        self.status_labels = []

        # Load RTSP URLs and extract IPs
        self.camera_data = self.load_camera_data()

        # Create clickable labels for each IP
        for ip, rtsp_url in self.camera_data:
            lbl = tk.Label(self.status_frame, text=f"{ip} - Kiểm tra...", font=("Arial", 12), cursor="hand2")
            lbl.pack(anchor="w", pady=2)
            # Bind click event to open ROI drawer
            lbl.bind("<Button-1>", lambda event, url=rtsp_url: self.open_roi_drawer(url))
            self.status_labels.append(lbl)

        # Refresh button
        self.btn_refresh = tk.Button(self.frame, text="🔄 Làm mới", command=self.refresh_status, font=("Arial", 12))
        self.btn_refresh.pack(pady=10)

        # Initial status check
        self.refresh_status()

    def load_camera_data(self):
        """Load RTSP URLs from config_be.json and extract IP addresses."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "overview/config_be.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                rtsp_urls = config.get("rtsp_urls", [])
                # Extract IP addresses from RTSP URLs using regex
                ip_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                return [(re.search(ip_pattern, url).group(1), url) for url in rtsp_urls if re.search(ip_pattern, url)]
        except Exception as e:
            print(f"Lỗi khi tải config_be.json: {e}")
            return []

    def is_online(self, ip: str) -> bool:
        """Check if a device is online using ping."""
        param = "-n" if platform.system().lower() == "windows" else "-c"
        command = ["ping", param, "1", ip]
        try:
            result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False

    def update_status(self, index, label):
        """Update the status of a single IP."""
        ip = self.camera_data[index][0]  # Get IP from camera_data
        online = self.is_online(ip)
        status_text = "🟢 Online" if online else "🔴 Offline"
        label.config(text=f"{ip} - {status_text}", foreground="green" if online else "red")

    def refresh_status(self):
        """Refresh the status of all IPs using threads."""
        if not self.camera_data:
            for label in self.status_labels:
                label.config(text="Không tìm thấy camera!", foreground="red")
            return

        for i, label in enumerate(self.status_labels):
            threading.Thread(target=self.update_status, args=(i, label), daemon=True).start()

    def open_roi_drawer(self, rtsp_url):
        """Open the BoundingBoxDrawer for the selected RTSP URL in a separate thread."""
        threading.Thread(target=self.run_roi_drawer, args=(rtsp_url,), daemon=True).start()

    def run_roi_drawer(self, rtsp_url):
        """Run the BoundingBoxDrawer for the given RTSP URL."""
        drawer = BoundingBoxDrawer(rtsp_url)
        drawer.run()

    def destroy(self):
        """Clean up resources when closing the tab."""
        self.frame.destroy()