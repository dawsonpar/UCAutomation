import logging
import os
import sys

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

# Configuration
MAX_RETRIES = 3  # Maximum number of retries for failed conversions


def process_file(
    drive_service, converter, file, machine_id, download_dir, output_dir, dng_folder_id
):
    """Process a single file with retry logic."""
    file_id = file["id"]
    file_name = file["name"]

    # Skip if already processed successfully
    if drive_service.is_file_processed(file_id):
        logging.info(f"Skipping {file_name} (ID: {file_id}), already processed")
        return True

    # Get current status
    status = drive_service.get_file_status(file_id)
    if status:
        retry_count = status.get("retry_count", 0)
        if status.get("status") == "failed" and retry_count >= MAX_RETRIES:
            logging.warning(
                f"Skipping {file_name} (ID: {file_id}), max retries exceeded"
            )
            return False

    # Try to mark as processing
    if not drive_service.mark_file_as_processing(file_id, machine_id):
        logging.info(
            f"Skipping {file_name} (ID: {file_id}), already being processed by another machine"
        )
        return False

    # Download the file
    local_path = os.path.join(download_dir, file_name)
    if not drive_service.download_file(file_id, local_path):
        error_msg = f"Failed to download {file_name} (ID: {file_id})"
        logging.error(error_msg)
        drive_service.mark_file_as_failed(
            file_id=file_id, machine_id=machine_id, error_message=error_msg
        )
        return False

    logging.info(f"Downloaded: {file_name} to {local_path}")

    # Convert the file
    try:
        converted = converter.convert(
            local_path, output_dir, file_id, already_marked=True
        )
        if not converted:
            error_msg = f"Failed to convert {file_name}"
            logging.error(error_msg)
            drive_service.mark_file_as_failed(
                file_id=file_id, machine_id=machine_id, error_message=error_msg
            )
            return False

        # Get the converted file path
        dng_file_name = os.path.splitext(file_name)[0] + ".dng"
        dng_file_path = os.path.join(output_dir, dng_file_name)

        # Upload the converted file to Google Drive
        uploaded_id = drive_service.upload_file(dng_file_path, dng_folder_id)
        if not uploaded_id:
            error_msg = f"Failed to upload {dng_file_name} to Google Drive"
            logging.error(error_msg)
            drive_service.mark_file_as_failed(
                file_id=file_id, machine_id=machine_id, error_message=error_msg
            )
            return False

        logging.info(f"Uploaded {dng_file_name} to Google Drive with ID: {uploaded_id}")

        # Mark as fully processed with additional info
        drive_service.mark_file_as_processed(
            file_id,
            machine_id,
            {
                "original_filename": file_name,
                "converted_filename": dng_file_name,
                "dng_file_id": uploaded_id,
            },
        )
        return True

    except Exception as e:
        error_msg = f"Failed to process {file_name}: {str(e)}"
        logging.error(error_msg)
        drive_service.mark_file_as_failed(
            file_id=file_id, machine_id=machine_id, error_message=error_msg
        )
        return False


def main():
    load_dotenv()
    logging.info("Starting raw converter")

    # Get required environment variables
    folder_id = os.environ.get("INGEST_FOLDER_ID")
    dng_folder_id = os.environ.get("DNG_FOLDER_ID")
    google_creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")

    # Validate required environment variables
    missing_vars = []
    if not folder_id:
        missing_vars.append("INGEST_FOLDER_ID")
    if not dng_folder_id:
        missing_vars.append("DNG_FOLDER_ID")
    if not google_creds_path:
        missing_vars.append("GOOGLE_CREDENTIALS_PATH")
    if not firebase_creds_path:
        missing_vars.append("FIREBASE_CREDENTIALS_PATH")

    if missing_vars:
        logging.error(
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
        logging.error(f"Failed to create directories: {e}")
        return

    try:
        # Initialize Google Drive service with Firestore integration
        drive_service = GoogleDriveService(
            folder_id=folder_id,
            credentials_path=google_creds_path,
            firebase_credentials_path=firebase_creds_path,
        )

        # Check storage quota before proceeding
        quota_info = drive_service.get_storage_quota()
        if not quota_info:
            logging.error("Failed to retrieve Drive storage quota information")
            return

        # Define a threshold for warning (90% of quota used)
        quota_threshold = 90.0
        if quota_info["usage_percentage"] > quota_threshold:
            logging.error(
                f"Drive storage quota critical: {quota_info['usage_percentage']:.2f}% used "
                f"({quota_info['usage'] / (1024 * 1024 * 1024):.2f} GB of {quota_info['limit'] / (1024 * 1024 * 1024):.2f} GB). "
                "Processing halted to prevent quota exceeded errors."
            )
            # Provide suggestions for clearing space
            logging.warning(
                "To free up space: 1) Empty trash 2) Delete unnecessary files "
                "3) Consider using a different service account"
            )
            return

        # Log current quota status
        logging.info(
            f"Drive storage status: {quota_info['usage_percentage']:.2f}% used "
            f"({quota_info['usage'] / (1024 * 1024 * 1024):.2f} GB of {quota_info['limit'] / (1024 * 1024 * 1024):.2f} GB)"
        )

        # Initialize the RawFileConverter with the same Firestore service
        converter = RawFileConverter(firestore_service=drive_service.firestore_service)

        # Get machine identifier for tracking
        machine_id = os.uname().nodename
        logging.info(f"Running on machine: {machine_id}")

        # Fetch files from Google Drive
        logging.info("Fetching file list from Google Drive")
        files = drive_service.list_files()

        # Filter for raw files
        raw_files = [
            file
            for file in files
            if file["name"].lower().endswith((".cr3", ".arw", ".nef"))
        ]
        logging.info(f"Found {len(raw_files)} raw files to process")

        # Process each file
        for file in raw_files:
            process_file(
                drive_service,
                converter,
                file,
                machine_id,
                download_dir,
                output_dir,
                dng_folder_id,
            )

    except Exception as e:
        logging.error(f"An error occurred in the main script: {str(e)}")

    logging.info("Script execution completed")


if __name__ == "__main__":
    main()
