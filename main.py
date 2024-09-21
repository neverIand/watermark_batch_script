import os
import gui
from DirectoryWatcher import Watcher

default_working_dir = '_target_'
default_watermark_path = os.path.join(os.path.dirname(os.path.abspath(default_working_dir)), default_working_dir,
                                      'watermark.png')

DEFAULT_CONFIG = {
    'unrar_tool': 'C:\\Program Files\\WinRAR\\UnRAR.exe',  # TODO: improve default UbRAR path
    'WORKING_DIR': default_working_dir,
    'WATERMARK_FILE': default_watermark_path,
    'WATERMARK_SIZE': 200,
    'WATERMARK_OPACITY': 0.75,
    'OUTPUT_HEIGHT': 1200,
    'OUTPUT_QUALITY': 80,
    'PAGE_IGNORE_COUNT': 2,
    'MAX_WORKERS': (os.cpu_count() or 4) * 2 - 1  # Example formula for I/O-bound tasks
}


def main():
    path_to_watch = DEFAULT_CONFIG['WORKING_DIR']
    # os.chmod(path_to_watch, 0o777)  # set the dir to readable, writable and executable
    print(f"Worker count: {DEFAULT_CONFIG['MAX_WORKERS']}")
    w = Watcher(path_to_watch, config=DEFAULT_CONFIG)
    w.run()


if __name__ == '__main__':
    # main()
    gui.start_watcher()

'''
Steps to take (MVP):
1. Put an .rar into a folder 
2. The script will unzip the .rar file (done)
3. Add a translucent png watermark to all the .png files in that folder
4. Compress all watermarked images into .jpg and make sure they are 1200 pixels height with the same aspect ratio as the original
5. Pack the processed images in to a folder and compress it into a zip file

TODO:
1. More configurations:
    - refactor: break up the file and move configs to main or a single file (done)
    - support .jpg
    - improve gui (more responsive layout)
'''
