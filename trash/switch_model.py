# import tkinter as tk
# from tkinter import messagebox

# class ROISetupWindow:
#     def __init__(self, master):
#         self.master = master
#         self.master.title("Thiết lập các ROI")
#         self.master.geometry("500x400")

#         self.roi_entries = []
#         self.limit_entries = []

#         self.frame = tk.Frame(master)
#         self.frame.pack(pady=10)

#         self.add_roi_row()  # Tạo sẵn 1 dòng đầu tiên

#         self.btn_add = tk.Button(master, text="➕ Thêm MODEL", command=self.add_roi_row, font=("Arial", 11))
#         self.btn_add.pack(pady=5)

#         self.btn_start = tk.Button(master, text="🚀 Bắt đầu", command=self.start_main_app, font=("Arial", 12, "bold"))
#         self.btn_start.pack(pady=10)

#     def add_roi_row(self):
#         row = len(self.roi_entries)

#         roi_label = tk.Label(self.frame, text=f"MODEL {row+1}:", font=("Arial", 11))
#         roi_label.grid(row=row, column=0, padx=5, pady=5)

#         roi_entry = tk.Entry(self.frame, font=("Arial", 11), width=20)
#         roi_entry.grid(row=row, column=1, padx=5)
#         self.roi_entries.append(roi_entry)

#         limit_entry = tk.Entry(self.frame, font=("Arial", 11), width=10)
#         limit_entry.grid(row=row, column=2, padx=5)
#         self.limit_entries.append(limit_entry)

#     def start_main_app(self):
#         rois = []
#         limits = []

#         for i in range(len(self.roi_entries)):
#             name = self.roi_entries[i].get().strip()
#             limit_str = self.limit_entries[i].get().strip()

#             if not name or not limit_str:
#                 continue
#             try:
#                 limit = int(limit_str)
#                 if limit <= 0:
#                     raise ValueError("Giới hạn phải > 0")
#             except:
#                 messagebox.showerror("Lỗi", f"Giới hạn không hợp lệ cho ROI '{name}'")
#                 return

#             rois.append(name)
#             limits.append(limit)

#         if not rois:
#             messagebox.showerror("Lỗi", "Phải nhập ít nhất một ROI hợp lệ.")
#             return

#         self.master.destroy()
#         root = tk.Tk()
#         ROISwitcherApp(root, rois, limits)
#         root.mainloop()

# class ROISwitcherApp:
#     def __init__(self, master, rois, limits):
#         self.master = master
#         self.master.title("ROI Request Manager")
#         self.master.geometry("500x320")

#         self.rois = rois
#         self.limits = limits
#         self.current_index = 0
#         self.request_count = 0

#         self.label_roi = tk.Label(master, text="", font=("Arial", 14, "bold"))
#         self.label_count = tk.Label(master, text="", font=("Arial", 12))
#         self.btn_request = tk.Button(master, text="Gửi Request", command=self.send_request, font=("Arial", 12))
#         self.log_text = tk.Text(master, height=6, state='disabled', font=("Courier", 10))

#         self.label_roi.pack(pady=10)
#         self.label_count.pack()
#         self.btn_request.pack(pady=10)
#         self.log_text.pack(padx=10, pady=10, fill=tk.BOTH)

#         self.update_display()

#     def send_request(self):
#         self.request_count += 1
#         self.log(f"Gửi request tới {self.get_current_roi()} ({self.request_count}/{self.get_current_limit()})")

#         if self.request_count >= self.get_current_limit():
#             self.log(f"🔁 ROI '{self.get_current_roi()}' đã đạt giới hạn. Chuyển sang ROI tiếp theo.")
#             self.switch_roi()

#         self.update_display()

#     def switch_roi(self):
#         if self.current_index < len(self.rois) - 1:
#             self.current_index += 1
#             self.request_count = 0
#         else:
#             self.log("✅ Đã sử dụng hết tất cả ROI.")
#             self.btn_request.config(state="disabled")

#     def get_current_roi(self):
#         return self.rois[self.current_index]

#     def get_current_limit(self):
#         return self.limits[self.current_index]

#     def update_display(self):
#         self.label_roi.config(text=f"Đang sử dụng: {self.get_current_roi()}")
#         self.label_count.config(text=f"Số request: {self.request_count} / {self.get_current_limit()}")

#     def log(self, msg):
#         self.log_text.config(state='normal')
#         self.log_text.insert(tk.END, f"{msg}\n")
#         self.log_text.see(tk.END)
#         self.log_text.config(state='disabled')


# # Chạy chương trình
# if __name__ == "__main__":
#     pre_root = tk.Tk()
#     ROISetupWindow(pre_root)
#     pre_root.mainloop()


import tkinter as tk
from tkinter import ttk

def create_main_ui():
    root = tk.Tk()
    root.title("Ứng dụng Quản lý Hệ thống")
    root.geometry("600x400")

    # Tạo Notebook (Tab control)
    tab_control = ttk.Notebook(root)

    # ===== Tab 1: Tổng quan =====
    tab1 = ttk.Frame(tab_control)
    tab_control.add(tab1, text='📊 Tổng quan')

    lbl1 = tk.Label(tab1, text='Đây là tab Tổng quan', font=('Arial', 14))
    lbl1.pack(pady=20)

    # ===== Tab 2: Quản lý ROI =====
    tab2 = ttk.Frame(tab_control)
    tab_control.add(tab2, text='🧭 Quản lý ROI')

    lbl2 = tk.Label(tab2, text='Tab Quản lý ROI - nơi hiển thị hoặc điều chỉnh ROI', font=('Arial', 14))
    lbl2.pack(pady=20)

    # ===== Tab 3: Cấu hình =====
    tab3 = ttk.Frame(tab_control)
    tab_control.add(tab3, text='⚙️ Cấu hình hệ thống')

    lbl3 = tk.Label(tab3, text='Tab cấu hình hệ thống', font=('Arial', 14))
    lbl3.pack(pady=20)

    # Hiển thị tab control
    tab_control.pack(expand=1, fill='both')

    root.mainloop()

create_main_ui()
