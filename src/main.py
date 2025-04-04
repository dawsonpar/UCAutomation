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
            file_id = file["id"]

            # Skip already processed files
            if drive_service.is_file_processed(file_id):
                logging.info(
                    f"Skipping {file['name']} (ID: {file_id}), already processed"
                )
                continue

            # Try to mark as processing, skip if already being processed elsewhere
            if not drive_service.mark_file_as_processing(file_id, machine_id):
                logging.info(
                    f"Skipping {file['name']} (ID: {file_id}), already being processed by another machine"
                )
                continue

            # Download the file
            local_path = os.path.join(download_dir, file["name"])
            if drive_service.download_file(file_id, local_path):
                logging.info(f"Downloaded: {file['name']} to {local_path}")

                # Convert the file
                try:
                    converted = converter.convert(
                        local_path, output_dir, file_id, already_marked=True
                    )

                    if converted:
                        # Get the converted file path
                        dng_file_name = os.path.splitext(file["name"])[0] + ".dng"
                        dng_file_path = os.path.join(output_dir, dng_file_name)

                        # Upload the converted file to Google Drive
                        uploaded_id = drive_service.upload_file(
                            dng_file_path, dng_folder_id
                        )
                        if uploaded_id:
                            logging.info(
                                f"Uploaded {dng_file_name} to Google Drive with ID: {uploaded_id}"
                            )

                            # Mark as fully processed with additional info
                            drive_service.mark_file_as_processed(
                                file_id,
                                machine_id,
                                {
                                    "original_filename": file["name"],
                                    "converted_filename": dng_file_name,
                                    "dng_file_id": uploaded_id,
                                },
                            )
                        else:
                            logging.error(
                                f"Failed to upload {dng_file_name} to Google Drive.\n"
                                "HINT: Does drive-automation@ucautomation.iam.gserviceaccount.com have permission to access the destination folder?"
                            )
                except Exception as e:
                    logging.error(f"Failed to convert {file['name']}: {str(e)}")
            else:
                logging.error(f"Failed to download {file['name']} (ID: {file_id})")

    except Exception as e:
        logging.error(f"An error occurred in the main script: {str(e)}")

    logging.info("Script execution completed")


if __name__ == "__main__":
    main()
