import os
import shutil
import time
import py7zr
import rarfile
import zipfile
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor
from utils import apply_watermark, compress_image, compress_and_move_folder, support_gbk


class Handler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

    def on_any_event(self, event):
        if event.is_directory or not event.event_type == 'created':
            return None

        if event.src_path.endswith('.rar'):
            print(f"RAR file detected: {event.src_path}")
            Handler.extract_rar(self, event.src_path)
        elif event.src_path.endswith('.7z'):
            print(f"7z file detected: {event.src_path}")
            self.extract_7z(event.src_path)
        elif event.src_path.endswith('.zip'):
            print(f"ZIP file detected: {event.src_path}")
            self.extract_zip(event.src_path)

    def extract_rar(self, file_path):
        # Initial delay for file write completion
        time.sleep(2)

        target_directory = os.path.dirname(os.path.abspath(file_path))
        try:
            with rarfile.RarFile(file_path) as rf:
                rf.extractall(target_directory)
            print(f"Extracted: {file_path}")

            extracted_subdir = self.determine_extracted_subdirectory(file_path, target_directory)
            if extracted_subdir:
                self.process_extracted_files(extracted_subdir, target_directory, file_path)

            # Moving the original .rar file after processing (duplicate step)
            # self.move_original_file(file_path, target_directory)

        except Exception as e:
            print(f"Error during extraction or processing: {e}")

    def extract_7z(self, file_path):
        # Initial delay for file write completion
        time.sleep(2)

        target_directory = os.path.dirname(os.path.abspath(file_path))
        try:
            with py7zr.SevenZipFile(file_path, mode='r') as z:
                z.extractall(path=target_directory)
            print(f"Extracted: {file_path}")

            extracted_subdir = self.determine_extracted_subdirectory(file_path, target_directory)
            if extracted_subdir:
                self.process_extracted_files(extracted_subdir, target_directory, file_path)

            # Move the original .7z file after processing
            # self.move_original_file(file_path, target_directory)

        except py7zr.exceptions.ArchiveError as e:
            # This catches errors specific to 7z archives
            print(f"Error during 7z extraction: {e}")

        except Exception as e:
            # This catches any other general exception
            print(f"Unexpected error during 7z extraction: {e}")

    def extract_zip(self, file_path):
        time.sleep(2)  # Delay to ensure the file is not being written to

        target_directory = os.path.dirname(os.path.abspath(file_path))
        try:
            with support_gbk(zipfile.ZipFile(file_path, 'r')) as zip_ref:
                zip_ref.extractall(target_directory)
            print(f"Extracted: {file_path}")

            extracted_subdir = self.determine_extracted_subdirectory(file_path, target_directory)
            if extracted_subdir:
                self.process_extracted_files(extracted_subdir, target_directory, file_path)

        except Exception as e:
            print(f"Error during ZIP extraction: {e}")

    def determine_extracted_subdirectory(self, file_path, target_directory):
        extracted_subdir = None

        # Handling for RAR files
        if file_path.endswith('.rar'):
            with rarfile.RarFile(file_path) as archive_file:
                all_names = [f.filename for f in archive_file.infolist()]
                first_extracted_file = all_names[0] if all_names else None

        # Handling for 7z files
        elif file_path.endswith('.7z'):
            with py7zr.SevenZipFile(file_path, mode='r') as archive_file:
                all_names = archive_file.getnames()
                first_extracted_file = next(iter(all_names), None)

        # Handling for ZIP files
        elif file_path.endswith('.zip'):
            with support_gbk(zipfile.ZipFile(file_path, 'r')) as archive_file:
                all_names = archive_file.namelist()
                first_extracted_file = next(iter(all_names), None)

        else:
            print(f"Unsupported file type: {file_path}")
            return None

        if first_extracted_file:
            # Attempt to find a common base directory if there is one
            common_dir = os.path.commonprefix(all_names).rstrip("/\\")
            if common_dir:
                # For archives where a common directory exists
                extracted_subdir = os.path.join(target_directory, common_dir)
            else:
                # For archives without a common subdirectory, or if the archive is flat
                extracted_dir_path = os.path.dirname(first_extracted_file) or ""
                if extracted_dir_path:
                    extracted_subdir = os.path.join(target_directory, extracted_dir_path)
                else:
                    # Default to the target directory if the first file is at the root
                    extracted_subdir = target_directory

        # Debug prints
        print("Target Directory:", target_directory)
        print("Extracted Directory Path:", extracted_subdir if extracted_subdir else "N/A")

        return extracted_subdir

    def process_extracted_files(self, extracted_subdir, target_directory, file_path):
        """Process extracted files, apply watermark, compress images, etc."""
        png_files = [os.path.join(root, file)
                     for root, dirs, files in os.walk(extracted_subdir)
                     for file in files if file.lower().endswith('.png')]
        # Apply watermark and compress images using ThreadPoolExecutor
        # Sort files if needed
        # png_files.sort()

        # Ensure PAGE_IGNORE_COUNT is within valid range
        total_png_count = len(png_files)
        page_ignore_count = max(0, min(self.config['PAGE_IGNORE_COUNT'], total_png_count))

        # Apply watermark to the appropriate number of files
        if page_ignore_count > 0:
            images_to_watermark = png_files[:-page_ignore_count]
        else:
            images_to_watermark = png_files

        # Using ThreadPoolExecutor to apply watermark in parallel
        with ThreadPoolExecutor(max_workers=self.config['MAX_WORKERS']) as executor:
            watermark_futures = [executor.submit(apply_watermark, image_path, target_directory,
                                                 self.config['WATERMARK_SIZE'], self.config['WATERMARK_FILE'])
                                 for image_path in images_to_watermark]

        # Optionally, you can wait for all futures to complete
        for future in watermark_futures:
            future.result()

        # Compress all images into JPG format
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
        print(f"Original file moved to: {new_location}")

        # Determine the final destination directory for the zip file (outside _target_)
        final_zip_directory = ""  # Replace with your desired path (!Not used at the moment)
        zip_name = os.path.basename(extracted_subdir)  # Example: use the name of the extracted folder
        # print(f"zip_name: {zip_name}")

        # Call the function to compress and move the folder
        compress_and_move_folder(extracted_subdir, final_zip_directory, zip_name)

    def move_original_file(self, file_path, target_directory):
        """Move the original RAR file after processing."""
        parent_directory = os.path.dirname(target_directory)
        new_location = os.path.join(parent_directory, os.path.basename(file_path))
        shutil.move(file_path, new_location)
        print(f"Original .rar file moved to: {new_location}")
