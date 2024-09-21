import os
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

        path_to_watch = DEFAULT_CONFIG['WORKING_DIR']  # hardcoded at the moment
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
        start_button.config(state='normal')  # Re-enable start button
        stop_button.config(state='disabled')  # Re-disable stop button
        print("Watcher stopped")


def select_unrar_tool_path():
    path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
    # handle empty input (e.g. user clicked cancel and did not pick anything)
    if path:
        unrar_tool_entry.delete(0, tk.END)
        unrar_tool_entry.insert(0, path)


def select_watermark_file_path():
    path = filedialog.askopenfilename(filetypes=[("Image files", "*.png")])
    # handle empty input (e.g. user clicked cancel and did not pick anything)
    if path:
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
root.geometry("600x300")  # Set an initial size
root.minsize(400, 300)  # Set a minimum size to prevent too small windows

# Path
# tk.Label(root, text="Path to Watch:").grid(row=0, column=0)
# path_entry = tk.Entry(root)
# path_entry.grid(row=0, column=1)
# tk.Button(root, text="Browse", command=select_path).grid(row=0, column=2)

# TODO: better input validation

# Define UI fields
fields = [
    {
        'label': "UnRAR Tool Path:",
        'variable': 'unrar_tool_entry',
        'default': DEFAULT_CONFIG['unrar_tool'],
        'browse': select_unrar_tool_path,
        'validate': None
    },
    {
        'label': "Watermark Path:",
        'variable': 'watermark_path_entry',
        'default': DEFAULT_CONFIG['WATERMARK_FILE'],
        'browse': select_watermark_file_path,
        'validate': None
    },
    {
        'label': "Watermark Size (px):",
        'variable': 'watermark_scale_entry',
        'default': str(DEFAULT_CONFIG['WATERMARK_SIZE']),
        'validate': validate_larger_than_zero
    },
    {
        'label': "Watermark Opacity (0~1):",
        'variable': 'watermark_opacity_entry',
        'default': str(DEFAULT_CONFIG['WATERMARK_OPACITY']),
        'validate': validate_between_zero_and_one
    },
    {
        'label': "Output Image Height (px):",
        'variable': 'output_height_entry',
        'default': str(DEFAULT_CONFIG['OUTPUT_HEIGHT']),
        'validate': validate_larger_than_zero
    },
    {
        'label': "Output Image Quality (1~100):",
        'variable': 'output_quality_entry',
        'default': str(DEFAULT_CONFIG['OUTPUT_QUALITY']),
        'validate': validate_between_one_and_one_hundred
    },
    {
        'label': "Number of Credit Page (>=0):",
        'variable': 'page_ignore_count_entry',
        'default': str(DEFAULT_CONFIG['PAGE_IGNORE_COUNT']),
        'validate': validate_larger_equal_than_zero
    }
]

# Dictionary to hold entry widgets
entries = {}

# Create UI elements dynamically
for idx, field in enumerate(fields):
    # Label
    tk.Label(root, text=field['label']).grid(row=idx, column=0, padx=5, pady=5, sticky='e')

    # Validation setup
    if field['validate']:
        vcmd = (root.register(field['validate']), '%P')
        entry = tk.Entry(root, validate="key", validatecommand=vcmd)
    else:
        entry = tk.Entry(root)

    entry.grid(row=idx, column=1, padx=5, pady=5, sticky='we')
    entry.insert(0, field['default'])
    entries[field['variable']] = entry

    # Browse button if applicable
    if 'browse' in field and field['browse']:
        browse_button = tk.Button(root, text="Browse", command=field['browse'])
        browse_button.grid(row=idx, column=2, padx=5, pady=5, sticky='w')

# Assign entries to variables
unrar_tool_entry = entries['unrar_tool_entry']
watermark_path_entry = entries['watermark_path_entry']
watermark_scale_entry = entries['watermark_scale_entry']
watermark_opacity_entry = entries['watermark_opacity_entry']
output_height_entry = entries['output_height_entry']
output_quality_entry = entries['output_quality_entry']
page_ignore_count_entry = entries['page_ignore_count_entry']

# Configure column weights for responsive design
root.columnconfigure(0, weight=0)  # Labels don't need to expand
root.columnconfigure(1, weight=1)  # Entries expand horizontally
root.columnconfigure(2, weight=0)  # Browse buttons don't need to expand

# Configure row weights for vertical responsiveness
for idx in range(len(fields)):
    root.rowconfigure(idx, weight=0)  # Fields have fixed height
root.rowconfigure(len(fields), weight=1)  # Extra space below fields

# Start and Stop buttons
button_frame = tk.Frame(root)
button_frame.grid(row=len(fields), column=0, columnspan=3, pady=10, sticky='ew')

# Make the button frame expand horizontally
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

start_button = tk.Button(button_frame, text="Start", command=start_watcher)
start_button.grid(row=0, column=0, padx=5, pady=5, sticky='e')

stop_button = tk.Button(button_frame, text="Stop", command=stop_watcher, state='disabled')
stop_button.grid(row=0, column=1, padx=5, pady=5, sticky='w')

# Optionally, add a status bar or additional widgets that can expand
# status_var = tk.StringVar(value="Ready")
# status_bar = tk.Label(root, textvariable=status_var, bd=1, relief='sunken', anchor='w')
# status_bar.grid(row=len(fields)+1, column=0, columnspan=3, sticky='we')

# Configure the status bar to expand horizontally
root.rowconfigure(len(fields) + 1, weight=0)

root.mainloop()
