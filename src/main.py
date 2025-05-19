import os

from dotenv import load_dotenv

from google_drive_service import GoogleDriveService
from log_config import get_logger
from raw_converter import RawFileConverter
from synology_service import SynologyService
from utils import (
    clean_download_directories,
    get_quota,
    get_quota_threshold,
    move_to_archive,
    process_file,
)

logger = get_logger()


def main():
    load_dotenv()
    logger.info("Starting raw converter")

    # Get required environment variables
    folder_id = os.environ.get("INGEST_FOLDER_ID")
    dng_folder_id = os.environ.get("DNG_FOLDER_ID")
    archive_folder_id = os.environ.get("ARCHIVE_FOLDER_ID")
    google_creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    nas_ip = os.environ.get("NAS_IP")
    nas_port = os.environ.get("NAS_PORT")
    nas_user = os.environ.get("NAS_USER")
    nas_pwd = os.environ.get("NAS_PWD")

    # Validate required environment variables
    missing_vars = []
    if not folder_id:
        missing_vars.append("INGEST_FOLDER_ID")
    if not dng_folder_id:
        missing_vars.append("DNG_FOLDER_ID")
    if not archive_folder_id:
        missing_vars.append("ARCHIVE_FOLDER_ID")
    if not google_creds_path:
        missing_vars.append("GOOGLE_CREDENTIALS_PATH")
    if not firebase_creds_path:
        missing_vars.append("FIREBASE_CREDENTIALS_PATH")
    if not nas_ip:
        missing_vars.append("NAS_IP")
    if not nas_port:
        missing_vars.append("NAS_PORT")
    if not nas_user:
        missing_vars.append("NAS_USER")
    if not nas_pwd:
        missing_vars.append("NAS_PWD")

    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        return

    # Setup directories
    home_dir = os.path.expanduser("~")
    base_dir = os.path.join(home_dir, "UCAutomation")
    download_dir = os.path.join(base_dir, "downloads/raw_files")
    output_dir = os.path.join(base_dir, "downloads/dng_files")

    try:
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return

    # Clean up old files in download directories
    raw_cleaned, dng_cleaned = clean_download_directories(base_dir)
    if raw_cleaned > 0 or dng_cleaned > 0:
        logger.info(f"Cleaned up {raw_cleaned} raw files and {dng_cleaned} DNG files")

    try:
        base_url = f"https://{nas_ip}:{nas_port}/webapi"
        print(f"BASE_URL: {base_url}")
        synology_service = SynologyService(firebase_creds_path)

        api_info = synology_service.get_api_info(base_url)
        print(f"API_INFO: {api_info}")
    # try:
    #     # Initialize Google Drive service with Firestore integration
    #     drive_service = GoogleDriveService(
    #         folder_id=folder_id,
    #         credentials_path=google_creds_path,
    #         firebase_credentials_path=firebase_creds_path,
    #     )

    #     # Check storage quota before proceeding
    #     quota_info = get_quota()
    #     if not get_quota_threshold(quota_info):
    #         return

    #     # Initialize the RawFileConverter with the same Firestore service
    #     converter = RawFileConverter(firestore_service=drive_service.firestore_service)

    #     # Get machine identifier for tracking
    #     machine_id = os.uname().nodename
    #     logger.info(f"Running on machine: {machine_id}")

    #     # Fetch files from Google Drive
    #     logger.info("Fetching file list from Google Drive")
    #     files = drive_service.list_files()

    #     # Filter for raw files
    #     raw_files = [
    #         file
    #         for file in files
    #         if file["name"].lower().endswith((".cr3", ".arw", ".nef"))
    #     ]
    #     logger.info(f"Found {len(raw_files)} raw files to process")

    #     # Process each file
    #     for file in raw_files:
    #         process_file(
    #             drive_service,
    #             converter,
    #             file,
    #             machine_id,
    #             download_dir,
    #             output_dir,
    #             dng_folder_id,
    #         )

    #         move_to_archive(drive_service, file, archive_folder_id)

    except Exception as e:
        logger.error(f"An error occurred in the main script: {str(e)}")

    logger.info("Script execution completed")


if __name__ == "__main__":
    main()
