from DirectoryWatcher import Watcher

CONFIG = {
    'WATERMARK_SCALE': 0.075,
    'WATERMARK_OPACITY': 0.45,
    'OUTPUT_HEIGHT': 1200,
    'OUTPUT_QUALITY': 80,
    'PAGE_IGNORE_COUNT': 2
}


def main():
    path_to_watch = "_target_"
    # os.chmod(path_to_watch, 0o777)  # set the dir to readable, writable and executable
    w = Watcher(path_to_watch, config=CONFIG)
    w.run()


if __name__ == '__main__':
    main()

'''
Steps to take (MVP):
1. Put an .rar into a folder 
2. The script will unzip the .rar file (done)
3. Add a translucent png watermark to all the .png files in that folder
4. Compress all watermarked images into .jpg and make sure they are 1200 pixels height with the same aspect ratio as the original
5. Pack the processed images in to a folder and compress it into a zip file

TODO:
1. More configurations:
    - refactor: break up the file and move configs to main or a single file
    - support .jpg
    - multithreading for adding watermark and compressing image

2. Add a GUI

3. Batch process (multiple rar files?)
'''
