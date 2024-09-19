import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from DirectoryWatcher import Watcher
from main import DEFAULT_CONFIG

# Global variable for the watcher thread
watcher_thread = None
watcher = None


# TODO: handle the final input value error and display the error message
def start_watcher():
    global watcher_thread, watcher
    try:
        config = {
            'unrar_tool': unrar_tool_entry.get(),
            'WATERMARK_FILE': watermark_path_entry.get(),
            'WATERMARK_SIZE': int(watermark_scale_entry.get()),
            'WATERMARK_OPACITY': float(watermark_opacity_entry.get()),
            'OUTPUT_HEIGHT': int(output_height_entry.get()),
            'OUTPUT_QUALITY': int(output_quality_entry.get()),
            'PAGE_IGNORE_COUNT': int(page_ignore_count_entry.get()),
            'MAX_WORKERS': (os.cpu_count() or 4) * 2 - 1  # Example formula for I/O-bound tasks
        }
        print(config)

        # TODO: unify this path
        path_to_watch = "_target_"
        watcher = Watcher(path_to_watch, config)

        # Run watcher in a separate thread
        watcher_thread = threading.Thread(target=watcher.run, daemon=True)
        watcher_thread.start()
        start_button.config(state='disabled')
        stop_button.config(state='normal')
        # sys.exit()  # Exit the script

    except ValueError as e:
        messagebox.showerror("Error", str(e))


def stop_watcher():
    global watcher_thread, watcher
    # print(watcher_thread, watcher)
    if watcher_thread and watcher:
        watcher.stop()  # Stop the watcher
        watcher_thread.join()  # Wait for the thread to finish
        watcher_thread = None
        watcher = None  # Reset the watcher instance
        start_button.config(state='normal')  # Re-enable the start button
        print("Watcher stopped")


def select_unrar_tool_path():
    path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    # handle empty input (e.g. user clicked cancel and did not pick anything)
    if path != '':
        unrar_tool_entry.delete(0, tk.END)
        unrar_tool_entry.insert(0, path)


def select_watermark_file_path():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png")])
    # handle empty input (e.g. user clicked cancel and did not pick anything)
    if path != '':
        watermark_path_entry.delete(0, tk.END)
        watermark_path_entry.insert(0, path)


def validate_larger_than_zero(v):
    if v == '':
        return True  # Allow empty temporary input
    try:
        num = float(v)
        return num > 0
    except ValueError:
        return False


def validate_larger_equal_than_zero(v):
    if v == '':
        return True  # Allow empty temporary input
    try:
        num = float(v)
        return num >= 0
    except ValueError:
        return False


def validate_between_zero_and_one(v):
    if v == '':
        return True  # Allow empty temporary input
    try:
        num = float(v)
        return 0 <= num <= 1
    except ValueError:
        return False


def validate_between_one_and_one_hundred(v):
    if v == '':
        return True  # Allow empty temporary input
    try:
        num = float(v)
        return 1 <= num <= 100
    except ValueError:
        return False


root = tk.Tk()
root.title("Script Configuration")

# Path
# tk.Label(root, text="Path to Watch:").grid(row=0, column=0)
# path_entry = tk.Entry(root)
# path_entry.grid(row=0, column=1)
# tk.Button(root, text="Browse", command=select_path).grid(row=0, column=2)

# TODO: better input validation

# TODO: replace hardcoded row and column using a for loop

# UnRAR Tool Path
tk.Label(root, text="UnRAR Tool Path:").grid(row=0, column=0)
unrar_tool_entry = tk.Entry(root)
unrar_tool_entry.grid(row=0, column=1)
tk.Button(root, text="Browse", command=select_unrar_tool_path).grid(row=0, column=2)
unrar_tool_entry.insert(0, DEFAULT_CONFIG['unrar_tool'])

# Watermark File Path
tk.Label(root, text="Watermark Path:").grid(row=1, column=0)
watermark_path_entry = tk.Entry(root)
watermark_path_entry.grid(row=1, column=1)
tk.Button(root, text="Browse", command=select_watermark_file_path).grid(row=1, column=2)
watermark_path_entry.insert(0, DEFAULT_CONFIG['WATERMARK_FILE'])

# TODO increase row count (manually)

# Watermark Size Entry
tk.Label(root, text="Watermark Size (px):").grid(row=2, column=0)
watermark_scale_entry = tk.Entry(root, validate="key", validatecommand=(root.register(validate_larger_than_zero), '%P'))
watermark_scale_entry.grid(row=2, column=1)
# Setting default value
watermark_scale_entry.insert(0, str(DEFAULT_CONFIG['WATERMARK_SIZE']))

# Watermark Opacity
tk.Label(root, text="Watermark Opacity (0~1):").grid(row=3, column=0)
watermark_opacity_entry = tk.Entry(root, validate="key",
                                   validatecommand=(root.register(validate_between_zero_and_one), '%P'))
watermark_opacity_entry.grid(row=3, column=1)
watermark_opacity_entry.insert(0, str(DEFAULT_CONFIG['WATERMARK_OPACITY']))

# Output image height in pixels
tk.Label(root, text="Output Image Height (pixel):").grid(row=4, column=0)
output_height_entry = tk.Entry(root, validate="key",
                               validatecommand=(root.register(validate_larger_than_zero), '%P'))
output_height_entry.grid(row=4, column=1)
output_height_entry.insert(0, str(DEFAULT_CONFIG['OUTPUT_HEIGHT']))

# Output image quality
tk.Label(root, text="Output Image Quality (1~100):").grid(row=5, column=0)
output_quality_entry = tk.Entry(root, validate="key",
                                validatecommand=(root.register(validate_between_one_and_one_hundred), '%P'))
output_quality_entry.grid(row=5, column=1)
output_quality_entry.insert(0, str(DEFAULT_CONFIG['OUTPUT_QUALITY']))

# Number of credit page
tk.Label(root, text="Number of Credit Page (>=0):").grid(row=6, column=0)
page_ignore_count_entry = tk.Entry(root, validate="key",
                                   validatecommand=(root.register(validate_larger_equal_than_zero), '%P'))
page_ignore_count_entry.grid(row=6, column=1)
page_ignore_count_entry.insert(0, str(DEFAULT_CONFIG['PAGE_IGNORE_COUNT']))

# Start Button
start_button = tk.Button(root, text="Start", command=start_watcher)
start_button.grid(row=7, column=1)

# Stop Button
stop_button = tk.Button(root, text="Stop", command=stop_watcher)
stop_button.grid(row=7, column=2)
stop_button.config(state='disabled')

root.mainloop()
