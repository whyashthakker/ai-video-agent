import zipfile
import os


def zip_directory(directory_path, zip_path):
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory_path):
            # Zip the mp3 folder
            if "mp3" in root:
                for file in files:
                    full_path = os.path.join(root, file)
                    if os.path.exists(full_path):
                        zipf.write(
                            full_path, os.path.relpath(full_path, directory_path)
                        )

            # Zip .jpg files only
            for file in files:
                if file.endswith(".jpg"):
                    full_path = os.path.join(root, file)
                    if os.path.exists(full_path):
                        zipf.write(
                            full_path, os.path.relpath(full_path, directory_path)
                        )
