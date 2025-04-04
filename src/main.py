import logging
import os

from dotenv import load_dotenv

from google_drive_service import GoogleDriveService
from raw_converter import RawFileConverter

# Configure logging
log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main():
    load_dotenv()
    logging.info("Starting raw converter")

    folder_id = os.environ.get("INGEST_FOLDER_ID")
    dng_folder_id = os.environ.get("DNG_FOLDER_ID")

    print(str(folder_id))
    print(str(dng_folder_id))

    # home_dir = os.path.expanduser("~")
    # base_dir = os.path.join(home_dir, "UCAutomation")

    # download_dir = os.path.join(base_dir, "downloads/raw_files")
    # output_dir = os.path.join(base_dir, "downloads/dng_files")
    # processed_files_path = os.path.join(base_dir, "lib/processed_files.json")

    # try:
    #     os.makedirs(download_dir, exist_ok=True)
    #     os.makedirs(output_dir, exist_ok=True)
    # except Exception as e:
    #     logging.error(f"Failed to create directories: {e}")
    #     return

    # drive_service = GoogleDriveService(folder_id, processed_files_path)
    # converter = RawFileConverter(processed_files_path)

    # logging.info("Fetching file list from Google Drive.")
    # files = drive_service.list_files()

    # raw_files = [
    #     file
    #     for file in files
    #     if file["name"].lower().endswith((".cr3", ".arw", ".nef"))
    # ]

    # for file in raw_files:
    #     local_path = os.path.join(download_dir, file["name"])

    #     # download file
    #     if drive_service.download_file(file["id"], local_path):
    #         logging.info(f"Downloaded: {file['name']} to {local_path}")

    #         # convert file
    #         try:
    #             converted = converter.convert(local_path, output_dir)

    #             if converted:
    #                 # Get the converted file path
    #                 dng_file_name = os.path.splitext(file["name"])[0] + ".dng"
    #                 dng_file_path = os.path.join(output_dir, dng_file_name)

    #                 # Upload the converted file to Google Drive
    #                 try:
    #                     drive_service.upload_file(dng_file_path, dng_folder_id)
    #                     logging.info(f"Uploaded {dng_file_name} to Google Drive.")
    #                 except Exception as e:
    #                     logging.error(
    #                         f"Failed to upload {dng_file_name} to Google Drive: {e}\n"
    #                         + "HINT: Does drive-automation@ucautomation.iam.gserviceaccount.com have permission to access the destination folder?"
    #                     )

    #         except Exception as e:
    #             logging.error(f"Failed to convert {file['name']}: {e}")

    # logging.info("Script execution completed.")


if __name__ == "__main__":
    main()
