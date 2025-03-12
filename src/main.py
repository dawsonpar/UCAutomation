import os

from google_drive_service import GoogleDriveService
from raw_converter import RawFileConverter, RawFileHandler


def main():
    folder_id = "1p6i00JY5lnYBzapVSKHtyd5IRFABuSTA"  # api-test folder
    dng_folder_id = "1ZJSh2_cjeFOTNtVMPix7ouE0BZoXSbHS"
    processed_files_path = "lib/processed_files.json"
    download_dir = "downloads/raw_files"
    output_dir = "downloads/dng_files"

    os.makedirs(download_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    drive_service = GoogleDriveService(folder_id, processed_files_path)
    converter = RawFileConverter(processed_files_path)
    raw_file_handler = RawFileHandler(converter)

    files = drive_service.list_files()

    raw_files = [
        file
        for file in files
        if file["name"].lower().endswith((".cr3", ".arw", ".nef"))
    ]

    for file in raw_files:
        local_path = os.path.join(download_dir, file["name"])

        # download file
        if drive_service.download_file(file["id"], local_path):
            print(f"Downloaded: {file['name']} to {local_path}")

            # convert file
            try:
                converted = converter.convert(local_path, output_dir)

                if converted:
                    # Get the converted file path
                    dng_file_name = os.path.splitext(file["name"])[0] + ".dng"
                    dng_file_path = os.path.join(output_dir, dng_file_name)

                    # Upload the converted file to Google Drive
                    try:
                        drive_service.upload_file(dng_file_path, dng_folder_id)
                    except Exception as e:
                        print(
                            f"Failed to upload {dng_file_name} to Google Drive: {e}\n"
                            + "HINT: Does drive-automation@ucautomation.iam.gserviceaccount.com have permission to access the destination folder?"
                        )

            except Exception as e:
                print(f"Failed to convert {file['name']}: {e}")


if __name__ == "__main__":
    main()
