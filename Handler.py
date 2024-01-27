import os
import shutil
import time

import rarfile
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor
from utils import apply_watermark, compress_image, compress_and_move_folder


class Handler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

    def on_any_event(self, event):
        if event.is_directory or not event.event_type == 'created':
            return None

        if event.src_path.endswith('.rar'):
            print(f"RAR file detected: {event.src_path}")
            Handler.extract_rar(self, event.src_path, self.config['PAGE_IGNORE_COUNT'])

    def extract_rar(self, file_path, page_ignore_count):
        # Wait for a short period to ensure file is not being written to
        time.sleep(2)

        target_directory = os.path.dirname(os.path.abspath(file_path))
        file_name = os.path.basename(file_path)
        correct_path = os.path.join(target_directory, file_name)
        # print(f"target_directory: {target_directory}; file_name: {file_name}; correct_path: {correct_path}")

        # Check if file is writable
        if not os.access(correct_path, os.W_OK):
            print(f"File is not writable: {correct_path}")
            return

        try:
            with rarfile.RarFile(correct_path) as rf:
                rf.extractall(target_directory)
            print(f"Extracted: {correct_path}")

            # Determine the extracted subdirectory
            extracted_subdir = None
            with rarfile.RarFile(file_path) as rf:
                first_extracted_file = rf.infolist()[0]
                extracted_subdir = os.path.join(target_directory, os.path.dirname(first_extracted_file.filename))

            # Apply watermark to each PNG file in the extracted subdirectory
            if extracted_subdir:
                png_files = [os.path.join(root, file)
                             for root, dirs, files in os.walk(extracted_subdir)
                             for file in files if file.lower().endswith('.png')]

                # Sort files if needed
                # png_files.sort()

                # Ensure PAGE_IGNORE_COUNT is within valid range
                total_png_count = len(png_files)
                page_ignore_count = max(0, min(page_ignore_count, total_png_count))

                # Apply watermark to the appropriate number of files
                if page_ignore_count > 0:
                    images_to_watermark = png_files[:-page_ignore_count]
                else:
                    images_to_watermark = png_files

                # for image_path in images_to_watermark:
                #     apply_watermark(image_path, target_directory, self.config['WATERMARK_SCALE'])

                # Using ThreadPoolExecutor to apply watermark in parallel
                with ThreadPoolExecutor(max_workers=self.config['MAX_WORKERS']) as executor:
                    watermark_futures = [executor.submit(apply_watermark, image_path, target_directory,
                                                         self.config['WATERMARK_SCALE'])
                                         for image_path in images_to_watermark]

                # Optionally, you can wait for all futures to complete
                for future in watermark_futures:
                    future.result()

                # Compress all images into JPG format
                # for image_path in png_files:
                #     compress_image(image_path, self.config['OUTPUT_HEIGHT'], self.config['OUTPUT_QUALITY'])
                with ThreadPoolExecutor(max_workers=self.config['MAX_WORKERS']) as executor:
                    compress_futures = [executor.submit(compress_image, image_path, self.config['OUTPUT_HEIGHT'],
                                                        self.config['OUTPUT_QUALITY'])
                                        for image_path in png_files]
                for future in compress_futures:
                    future.result()

                # After processing, move the original .rar file to the parent directory
                parent_directory = os.path.dirname(target_directory)
                new_location = os.path.join(parent_directory, os.path.basename(file_path))
                shutil.move(file_path, new_location)
                print(f"Original .rar file moved to: {new_location}")

                # Determine the final destination directory for the zip file (outside _target_)
                final_zip_directory = ""  # Replace with your desired path
                zip_name = os.path.basename(extracted_subdir)  # Example: use the name of the extracted folder
                # print(f"zip_name: {zip_name}")

                # Call the function to compress and move the folder
                compress_and_move_folder(extracted_subdir, final_zip_directory, zip_name)

        except Exception as e:
            print(f"Error during extraction or processing: {e}")
