import os
import time
import rarfile
import zipfile
import shutil
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# TODO: make the path to UNRAR_TOOL configurable
rarfile.UNRAR_TOOL = 'C:\\Program Files\\WinRAR\\UnRAR.exe'  # Replace with the actual path

WATERMARK_SCALE = 0.075
WATERMARK_OPACITY = 0.45

OUTPUT_HEIGHT = 1200
OUTPUT_QUALITY = 80

PAGE_IGNORE_COUNT = 2


class Watcher:
    def __init__(self, directory_to_watch):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        print(f"Observer started. Monitoring {self.DIRECTORY_TO_WATCH}")
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


# TODO: make the path to watermarked image configurable
def apply_watermark(image_path, target_directory):
    watermark_path = os.path.join(target_directory, 'watermark.png')
    try:
        with Image.open(image_path) as base_image:
            with Image.open(watermark_path).convert("RGBA") as watermark:
                # Resize watermark to 15% of its original size
                watermark_size = tuple(int(dim * WATERMARK_SCALE) for dim in watermark.size)
                watermark = watermark.resize(watermark_size, Image.Resampling.LANCZOS)

                # Adjust watermark opacity to 45%
                watermark = watermark.copy()  # Create a copy to modify
                bands = list(watermark.split())
                bands[3] = bands[3].point(lambda x: x * 0.45)
                watermark = Image.merge('RGBA', bands)

                # Position watermark at the bottom-right corner of the base image
                watermark_position = (base_image.size[0] - watermark_size[0],
                                      base_image.size[1] - watermark_size[1])

                # Create a new image by combining base image and watermark
                base_image.paste(watermark, watermark_position, watermark)

                # Overwrite the original image
                base_image.save(image_path, "PNG")
                print(f"Watermark applied and original image replaced: {image_path}")

    except Exception as e:
        print(f"Error in applying watermark to {image_path}: {e}")


def compress_image(image_path, output_height=OUTPUT_HEIGHT):
    try:
        with Image.open(image_path) as img:
            # Calculate the target size maintaining the aspect ratio
            aspect_ratio = img.width / img.height
            output_width = int(output_height * aspect_ratio)

            # Resize the image
            resized_img = img.resize((output_width, output_height), Image.Resampling.LANCZOS)

            # Convert RGBA to RGB if necessary
            if resized_img.mode == 'RGBA':
                resized_img = resized_img.convert('RGB')

            # Define the output path for the JPG file
            output_path = os.path.splitext(image_path)[0] + '.jpg'

            # Save the image in JPG format
            resized_img.save(output_path, "JPEG", quality=OUTPUT_QUALITY)
            print(f"Image compressed and saved as: {output_path}")

            # Remove the original PNG file
            os.remove(image_path)
            print(f"Original image removed: {image_path}")

    except Exception as e:
        print(f"Error in compressing {image_path}: {e}")


def compress_and_move_folder(folder_to_compress, final_zip_directory, zip_name):
    # Create a temporary path for the zip file
    temp_zip_path = os.path.join(final_zip_directory, f"{zip_name}.zip")

    # Step 1: Compress the folder into a zip file
    try:
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(folder_to_compress):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Exclude the zip file itself
                    if file_path != temp_zip_path:
                        zipf.write(file_path, os.path.relpath(file_path, os.path.dirname(folder_to_compress)))

        print(f"Folder '{folder_to_compress}' is compressed into: {temp_zip_path}")

        # Step 2: Move the zip file to the parent directory of '_target_'
        target_parent_directory = os.path.dirname(os.path.dirname(folder_to_compress))
        final_zip_path = os.path.join(target_parent_directory, f"{zip_name}.zip")
        shutil.move(temp_zip_path, final_zip_path)
        print(f"Zip file moved to: {final_zip_path}")

        # Step 3: Delete the original folder after successful zipping
        shutil.rmtree(folder_to_compress)
        print(f"Original folder deleted: {folder_to_compress}")

    except Exception as e:
        print(f"Error during compression or folder deletion: {e}")


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory or not event.event_type == 'created':
            return None

        if event.src_path.endswith('.rar'):
            print(f"RAR file detected: {event.src_path}")
            Handler.extract_rar(event.src_path)

    @staticmethod
    def extract_rar(file_path):
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
                page_ignore_count = max(0, min(PAGE_IGNORE_COUNT, total_png_count))

                # Apply watermark to the appropriate number of files
                if page_ignore_count > 0:
                    images_to_watermark = png_files[:-page_ignore_count]
                else:
                    images_to_watermark = png_files

                for image_path in images_to_watermark:
                    apply_watermark(image_path, target_directory)

                # Compress all images into JPG format
                for image_path in png_files:
                    compress_image(image_path)

                # After processing, move the original .rar file to the parent directory
                parent_directory = os.path.dirname(target_directory)
                new_location = os.path.join(parent_directory, os.path.basename(file_path))
                shutil.move(file_path, new_location)
                print(f"Original .rar file moved to: {new_location}")

                # Determine the final destination directory for the zip file (outside _target_)
                final_zip_directory = ""  # Replace with your desired path
                zip_name = os.path.basename(extracted_subdir)  # Example: use the name of the extracted folder
                print(f"zip_name: {zip_name}")

                # Call the function to compress and move the folder
                compress_and_move_folder(extracted_subdir, final_zip_directory, zip_name)




        except Exception as e:
            print(f"Error during extraction or processing: {e}")
