import tkinter as tk
from tkinter import ttk

from overview.tab_overview.grid_camera import GridCameraTab
from overview.tab_config_roi.config_roi import ConfigRoiTab
from overview.tab_settings.settings import SettingsTab

def create_main_ui():
    root = tk.Tk()
    root.title("Ứng dụng Quản lý Hệ thống")
    root.geometry("1280x720")

    notebook = ttk.Notebook(root)

    # Tạo tab và gắn vào notebook
    GridCamera = GridCameraTab(notebook)
    ConfigROI = ConfigRoiTab(notebook)
    Settings = SettingsTab(notebook)

    notebook.add(GridCamera.frame, text="📊 Tổng quan")
    notebook.add(ConfigROI.frame, text="🧭 Quản lý ROI")
    notebook.add(Settings.frame, text="⚙️ Cấu hình")

    notebook.pack(expand=1, fill='both')
    root.mainloop()

if __name__ == "__main__":
    create_main_ui()
