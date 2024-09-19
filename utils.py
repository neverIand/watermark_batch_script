import os
import shutil
import zipfile
from zipfile import ZipFile
from PIL import Image


# TODO: remove unused variable, apply custom config for opacity


def apply_watermark(image_path, target_directory, watermark_width, watermark_file):
    """
    Applies a watermark to an image, resizing the watermark to 330px wide while maintaining aspect ratio.

    Parameters:
    - image_path (str): Path to the base image.
    - target_directory (str): Directory where the processed image will be saved.
    - watermark_file (str): Path to the watermark image.

    Returns:
    - None
    """
    # print('Watermark file:', watermark_file)
    watermark_path = watermark_file  # Removed dependency on target_directory

    try:
        with Image.open(image_path) as base_image:
            with Image.open(watermark_path).convert("RGBA") as watermark:
                # Define the desired watermark width
                desired_width = watermark_width  # TODO

                # Calculate the scaling factor to maintain aspect ratio
                original_width, original_height = watermark.size
                scaling_factor = desired_width / original_width
                new_height = int(original_height * scaling_factor)

                # Resize the watermark to the desired width while maintaining aspect ratio
                watermark = watermark.resize((desired_width, new_height), Image.Resampling.LANCZOS)

                # Adjust watermark opacity to 45%

                # Ensure the watermark has an alpha channel
                if watermark.mode != 'RGBA':
                    watermark = watermark.convert('RGBA')

                # Split the watermark into its component bands
                bands = list(watermark.split())
                # Modify the alpha band to set opacity to 45%
                bands[3] = bands[3].point(lambda x: x * 0.75)
                # Merge the bands back together
                watermark = Image.merge('RGBA', bands)

                # Position watermark at the bottom-right corner of the base image
                base_width, base_height = base_image.size
                watermark_width, watermark_height = watermark.size
                margin = 10  # Margin from the edges

                watermark_position = (
                    base_width - watermark_width - margin,
                    base_height - watermark_height - margin
                )

                # watermark_position = (0, 0) # testing only

                # Create a transparent layer the size of the base image to hold the watermark
                transparent = Image.new('RGBA', base_image.size)
                transparent.paste(watermark, watermark_position, watermark)

                # Combine the base image with the watermark
                combined = Image.alpha_composite(base_image.convert('RGBA'), transparent)

                # Ensure the target directory exists
                os.makedirs(target_directory, exist_ok=True)

                # Overwrite the original image
                combined.convert('RGB').save(image_path, "PNG")
                # print(f"Watermark applied and original image replaced: {image_path}")

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

            # Check if the image has an alpha channel
            if resized_img.mode == 'RGBA' or resized_img.mode == 'LA':
                # Create a white background image
                background = Image.new('RGB', resized_img.size, (255, 255, 255))
                # Composite the resized image onto the background
                # This checks if the image has an alpha channel and uses it as a mask
                background.paste(resized_img, mask=resized_img.getchannel('A'))  # Safely get the alpha channel
                resized_img = background
            else:
                # If not 'LA' or 'RGBA', convert other modes directly to 'RGB' (this includes 'L' mode)
                resized_img = resized_img.convert('RGB')

            # Define the output path for the JPG file
            output_path = os.path.splitext(image_path)[0] + '.jpg'

            # Save the image in JPG format
            resized_img.save(output_path, "JPEG", quality=output_quality)
            # print(f"Image compressed and saved as: {output_path}")

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
        # print(f"Original folder deleted: {folder_to_compress}")

    except Exception as e:
        print(f"Error during compression or folder deletion: {e}")


# credit: https://blog.csdn.net/qq_21076851/article/details/122752196
def support_gbk(zip_file: ZipFile):
    name_to_info = zip_file.NameToInfo

    for name, info in name_to_info.copy().items():
        real_name = name.encode('cp437').decode('gbk')
        if real_name != name:
            info.filename = real_name
            del name_to_info[name]
            name_to_info[real_name] = info
    return zip_file
