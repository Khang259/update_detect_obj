import zipfile
import json
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class InteractiveMapApp:
    def __init__(self, master):
        self.master = master
        master.title("Interactive Map Viewer")

        self.show_labels = tk.BooleanVar(value=True)
        self.show_distances = tk.BooleanVar(value=True)

        self.data = None
        self.press_event = None

        self.fig, self.ax = plt.subplots(figsize=(14, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_press)
        self.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.init_ui(master)

    def init_ui(self, root):
        frame = tk.Frame(root)
        frame.pack(side=tk.TOP, fill=tk.X)

        tk.Button(frame, text="Mở file ZIP", command=self.load_zip).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Checkbutton(frame, text="Hiện tên điểm", variable=self.show_labels, command=self.redraw).pack(side=tk.LEFT)
        tk.Checkbutton(frame, text="Hiện Δx/Δy", variable=self.show_distances, command=self.redraw).pack(side=tk.LEFT)

    def load_zip(self):
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if not path:
            return
        try:
            with zipfile.ZipFile(path, 'r') as zip_ref:
                json_file = next((f for f in zip_ref.namelist() if f.endswith("compress.json")), None)
                if not json_file:
                    raise FileNotFoundError("Không tìm thấy compress.json")
                with zip_ref.open(json_file) as f:
                    self.data = json.load(f)
            self.reset_view()
            self.redraw()
        except Exception as e:
            print(f"Lỗi khi đọc file: {e}")

    def reset_view(self):
        w = self.data['width']
        h = self.data['height']
        x0 = self.data['xAttrMin']
        y0 = self.data['yAttrMin']
        self.ax.set_xlim(x0, x0 + w)
        self.ax.set_ylim(y0, y0 + h)

    def redraw(self):
        if not self.data:
            return

        self.ax.clear()
        width = self.data['width']
        height = self.data['height']
        x_min = self.data['xAttrMin']
        y_min = self.data['yAttrMin']
        x_max = x_min + width
        y_max = y_min + height
        line_arr = self.data.get("lineArr", [])

        # Khung bản đồ
        self.ax.add_patch(plt.Rectangle((x_min, y_min), width, height,
                                        linewidth=1.2, edgecolor='gray', facecolor='whitesmoke', alpha=0.3))

        drawn_points = {}

        for line in line_arr:
            name_a, name_b = line[0], line[1]
            coords = line[6]

            for i in range(len(coords) - 1):
                x1, y1 = coords[i]
                x2, y2 = coords[i + 1]
                self.ax.plot([x1, x2], [y1, y2], color='red', linewidth=2)

                if self.show_distances.get():
                    dx, dy = x2 - x1, y2 - y1
                    self.ax.text((x1 + x2)/2, (y1 + y2)/2, f"Δx={dx}, Δy={dy}", fontsize=8, color='darkred')

            for i, (x, y) in enumerate(coords):
                point_name = name_a if i == 0 else (name_b if i == len(coords)-1 else None)
                if point_name and point_name not in drawn_points:
                    self.ax.plot(x, y, 'bo', markersize=5)
                    if self.show_labels.get():
                        self.ax.text(x + 1000, y + 1000, point_name, fontsize=9, color='blue')
                    drawn_points[point_name] = (x, y)

        self.ax.set_title("Bản đồ tương tác từ compress.json")
        self.ax.set_xlabel("Tọa độ X (m)")
        self.ax.set_ylabel("Tọa độ Y (m)")
        self.ax.grid(True, linestyle='--', alpha=0.3)

        self.canvas.draw()

    # ==== Zoom & Pan ====

    def on_scroll(self, event):
        base_scale = 1.02
        scale = base_scale if event.button == 'up' else 1/base_scale

        cur_xlim = self.ax.get_xlim()
        cur_ylim = self.ax.get_ylim()

        xdata = event.xdata
        ydata = event.ydata
        if xdata is None or ydata is None:
            return

        new_xlim = [xdata - (xdata - cur_xlim[0]) * scale,
                    xdata + (cur_xlim[1] - xdata) * scale]
        new_ylim = [ydata - (ydata - cur_ylim[0]) * scale,
                    ydata + (cur_ylim[1] - ydata) * scale]

        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw()

    def on_press(self, event):
        if event.button == 1:  # Left mouse
            self.press_event = event

    def on_release(self, event):
        self.press_event = None

    def on_motion(self, event):
        if self.press_event is None or event.button != 1:
            return

        dx = self.press_event.xdata - event.xdata
        dy = self.press_event.ydata - event.ydata

        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = InteractiveMapApp(root)
    root.geometry("1200x700")
    root.mainloop()
