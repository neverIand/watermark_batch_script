import os
import shutil
import zipfile

from PIL import Image


# TODO?: make the path to watermarked image configurable
def apply_watermark(image_path, target_directory, watermark_scale):
    watermark_path = os.path.join(target_directory, 'watermark.png')
    try:
        with Image.open(image_path) as base_image:
            with Image.open(watermark_path).convert("RGBA") as watermark:
                # Resize watermark to 15% of its original size
                watermark_size = tuple(int(dim * watermark_scale) for dim in watermark.size)
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


def compress_image(image_path, output_height, output_quality):
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
            resized_img.save(output_path, "JPEG", quality=output_quality)
            print(f"Image compressed and saved as: {output_path}")

            # Remove the original PNG file
            os.remove(image_path)
            # print(f"Original image removed: {image_path}")

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
