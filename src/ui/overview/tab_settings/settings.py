import tkinter as tk
import json
import os

class SettingsTab:
    def __init__(self, master):
        self.frame = tk.Frame(master)
        label = tk.Label(self.frame, text="Cấu hình hệ thống", font=("Arial", 14))
        label.pack(pady=20)

        # List to store RTSP entry widgets and their associated frames
        self.rtsp_entries = []
        
        # Frame for RTSP inputs and Add button
        self.rtsp_container = tk.Frame(self.frame)
        self.rtsp_container.pack(pady=5)

        # Add initial RTSP input field
        self.add_rtsp_field()

        # Button to add more RTSP fields
        self.add_rtsp_button = tk.Button(self.frame, text="Thêm RTSP URL", command=self.add_rtsp_field)
        self.add_rtsp_button.pack(pady=5)

        # Submit button for RTSP
        self.rtsp_submit_button = tk.Button(self.frame, text="Thêm Camera", command=self.store_settings)
        self.rtsp_submit_button.pack(pady=10)

        # Server URL input
        self.server_label = tk.Label(self.frame, text="Server URL:", font=("Arial", 12))
        self.server_label.pack(pady=5)

        self.server_entry = tk.Entry(self.frame, width=50)
        self.server_entry.pack(pady=5)
        self.server_entry.insert(0, "http://")  # Default placeholder for Server URL

        # Submit button for Server
        self.server_submit_button = tk.Button(self.frame, text="Thêm RCS_Server", command=self.store_settings)
        self.server_submit_button.pack(pady=10)

        # Feedback label to show success or error messages
        self.feedback_label = tk.Label(self.frame, text="", font=("Arial", 10), fg="green")
        self.feedback_label.pack(pady=5)

    def add_rtsp_field(self):
        # Create a frame to hold the RTSP entry and remove button
        rtsp_frame = tk.Frame(self.rtsp_container)
        rtsp_frame.pack(pady=2, fill=tk.X)

        # RTSP URL input
        rtsp_entry = tk.Entry(rtsp_frame, width=50)
        rtsp_entry.pack(side=tk.LEFT, padx=5)
        rtsp_entry.insert(0, "rtsp://")  # Default placeholder for RTSP URL

        # Remove button for this RTSP field
        remove_button = tk.Button(rtsp_frame, text="Xóa", command=lambda: self.remove_rtsp_field(rtsp_frame, rtsp_entry))
        remove_button.pack(side=tk.LEFT, padx=5)

        # Store the entry widget in the list
        self.rtsp_entries.append((rtsp_frame, rtsp_entry))

    def remove_rtsp_field(self, rtsp_frame, rtsp_entry):
        # Prevent removing the last RTSP field to ensure at least one remains
        if len(self.rtsp_entries) > 1:
            rtsp_frame.destroy()
            self.rtsp_entries.remove((rtsp_frame, rtsp_entry))
            self.feedback_label.config(text="Đã xóa RTSP URL!", fg="green")
        else:
            self.feedback_label.config(text="Phải có ít nhất một RTSP URL!", fg="red")

    def store_settings(self):
        rtsp_urls = [entry.get() for _, entry in self.rtsp_entries if entry.get() and entry.get() != "rtsp://"]
        server_url = self.server_entry.get()

        # Validate inputs
        if not rtsp_urls:
            self.feedback_label.config(text="Vui lòng nhập ít nhất một RTSP URL hợp lệ!", fg="red")
            return
        # if not server_url or server_url == "http://":
        #     self.feedback_label.config(text="Vui lòng nhập Server URL hợp lệ!", fg="red")
        #     return

        # Prepare data to save
        config_data = {
            "rtsp_urls": rtsp_urls,  # Changed to plural to store list
            "server_url": server_url
        }

        # Path to config_be.json (same level as main.py)
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config_be.json")

        try:
            # Save to config_be.json
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            self.feedback_label.config(text="Lưu cấu hình thành công!", fg="green")

            # Optionally, send RTSP URL to server
            #self.send_rtsp_to_server(rtsp_url, server_url)

        except Exception as e:
            self.feedback_label.config(text=f"Lỗi khi lưu cấu hình: {str(e)}", fg="red")

    # def send_rtsp_to_server(self, rtsp_url, server_url):
    #     try:
    #         payload = {"rtsp_url": rtsp_url}
    #         response = requests.post(server_url, json=payload)

    #         if response.status_code == 200:
    #             self.feedback_label.config(text="Thêm camera thành công!", fg="green")
    #             self.rtsp_entry.delete(0, tk.END)  # Clear RTSP input field
    #             self.rtsp_entry.insert(0, "rtsp://")  # Reset placeholder
    #         else:
    #             self.feedback_label.config(text=f"Lỗi server: {response.status_code}", fg="red")

    #     except requests.exceptions.RequestException as e:
    #         self.feedback_label.config(text=f"Lỗi kết nối: {str(e)}", fg="red")