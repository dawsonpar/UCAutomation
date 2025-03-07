import os

from google_drive_service import GoogleDriveService
from raw_converter import RawFileConverter, RawFileHandler


def main():
    folder_id = "1p6i00JY5lnYBzapVSKHtyd5IRFABuSTA"  # api-test folder
    processed_files_path = "src/processed_files.json"
    download_dir = "downloads/raw_files"
    output_dir = "downloads/dng_files"

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    drive_service = GoogleDriveService(folder_id, processed_files_path)
    converter = RawFileConverter()
    raw_file_handler = RawFileHandler(converter)

    files = drive_service.list_files()

    raw_files = [
        file
        for file in files
        if file["name"].lower().endswith((".cr3", ".arw", ".nef"))
    ]

    for file in raw_files:
        local_path = os.path.join(download_dir, file["name"])
        if drive_service.download_file(file["id"], local_path):
            print(f"Downloaded: {file['name']} to {local_path}")

            try:
                converter.convert(local_path, output_dir)
                print(f"Converted {file['name']} to DNG.")
            except Exception as e:
                print(f"Failed to convert {file['name']}: {e}")


if __name__ == "__main__":
    main()
