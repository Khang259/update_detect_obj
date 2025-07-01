import tkinter as tk
import json
import os
import cv2
import threading
from PIL import Image, ImageTk
import numpy as np

class GridCameraTab:
    def __init__(self, master):
        self.frame = tk.Frame(master)
        label = tk.Label(self.frame, text="Tổng quan hệ thống", font=("Arial", 14))
        label.pack(pady=20)

        # List to store video labels and thread control flags
        self.video_labels = []
        self.stop_threads = []
        self.threads = []

        # Load RTSP URLs from config_be.json
        self.rtsp_urls = self.load_rtsp_urls()

        # Create a grid for video streams
        self.grid_frame = tk.Frame(self.frame)
        self.grid_frame.pack(pady=10)

        # Start video streams in threads
        self.start_video_streams()

    def load_rtsp_urls(self):
        """Load RTSP URLs from config_be.json."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "overview/config_be.json")
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("rtsp_urls", [])
        except Exception as e:
            print(f"Error loading config_be.json: {e}")
            return []

    def start_video_streams(self):
        """Start a thread for each RTSP stream and display in a grid."""
        if not self.rtsp_urls:
            label = tk.Label(self.grid_frame, text="Không tìm thấy RTSP URLs!", font=("Arial", 12), fg="red")
            label.pack()
            return

        # Calculate grid layout (e.g., 2 columns for simplicity)
        cols = 2
        rows = (len(self.rtsp_urls) + cols - 1) // cols

        for i, rtsp_url in enumerate(self.rtsp_urls):
            # Create a label for the video stream
            video_label = tk.Label(self.grid_frame)
            video_label.grid(row=i // cols, column=i % cols, padx=5, pady=5)
            self.video_labels.append(video_label)

            # Thread control flag
            stop_flag = threading.Event()
            self.stop_threads.append(stop_flag)

            # Start a thread for this RTSP stream
            thread = threading.Thread(target=self.stream_video, args=(rtsp_url, video_label, stop_flag))
            thread.daemon = True  # Ensure thread stops when main program exits
            self.threads.append(thread)
            thread.start()

    def stream_video(self, rtsp_url, video_label, stop_flag):
        """Capture and display video stream in a separate thread."""
        try:
            # Initialize video capture
            cap = cv2.VideoCapture(rtsp_url)
            if not cap.isOpened():
                video_label.config(text=f"Lỗi: Không mở được {rtsp_url}", fg="red")
                return

            while not stop_flag.is_set():
                ret, frame = cap.read()
                if not ret:
                    video_label.config(text=f"Lỗi: Không đọc được khung hình từ {rtsp_url}", fg="red")
                    break

                # Resize frame to 640x480 for display
                frame = cv2.resize(frame, (320, 240))

                # Convert frame to RGB (OpenCV uses BGR)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image and then to PhotoImage
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)

                # Update label with new frame (thread-safe UI update)
                video_label.config(image=photo)
                video_label.image = photo  # Keep a reference to avoid garbage collection

            cap.release()

        except Exception as e:
            video_label.config(text=f"Lỗi: {str(e)}", fg="red")

    def destroy(self):
        """Clean up threads and resources when closing the tab."""
        # Signal all threads to stop
        for stop_flag in self.stop_threads:
            stop_flag.set()

        # Wait for all threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join()

        # Call the parent destroy method
        self.frame.destroy()