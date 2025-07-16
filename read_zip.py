import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import zipfile
import json
import os


def read_zip_and_show_json():
    zip_path = filedialog.askopenfilename(title="Chọn file .zip", filetypes=[("Zip files", "*.zip")])
    if not zip_path:
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            json_files = [f for f in zip_ref.namelist() if f.endswith('.json')]

            if not json_files:
                messagebox.showinfo("Không tìm thấy", "Không có file JSON nào trong file zip này.")
                return

            for json_file in json_files:
                content = zip_ref.read(json_file).decode('utf-8')
                try:
                    json_data = json.loads(content)
                    pretty_json = json.dumps(json_data, indent=4, ensure_ascii=False)
                except json.JSONDecodeError:
                    pretty_json = f"(Lỗi phân tích JSON trong file {json_file})\n\n{content}"

                add_tab(json_file, pretty_json)

    except zipfile.BadZipFile:
        messagebox.showerror("Lỗi", "File không phải là định dạng zip hợp lệ.")


def add_tab(filename, content):
    tab = tk.Frame(notebook)
    notebook.add(tab, text=os.path.basename(filename))

    text_widget = scrolledtext.ScrolledText(tab, wrap=tk.WORD, font=("Consolas", 10))
    text_widget.insert(tk.END, content)
    text_widget.config(state=tk.DISABLED)
    text_widget.pack(expand=True, fill='both')


# Giao diện chính
root = tk.Tk()
root.title("Zip JSON Viewer")
root.geometry("800x600")

top_frame = tk.Frame(root)
top_frame.pack(side="top", fill="x")

open_btn = tk.Button(top_frame, text="Mở file ZIP", command=read_zip_and_show_json)
open_btn.pack(pady=5)

from tkinter import ttk
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

root.mainloop()