import logging
import os
import shutil

from firestore_service import FirestoreService

# Configure logging
log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class SynologyService:
    def __init__(
        self, fire_base_credentials_path=None, collection_name="processed_files"
    ):
        self.firestore_service = FirestoreService(
            collection_name=collection_name,
            credentials_path=fire_base_credentials_path,
        )

    def upload_file(self, file_path, folder_path):
        """Uploads a file to Synology NAS."""
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None

        try:
            # Create the destination folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)

            # Upload the file
            shutil.copy2(
                file_path, os.path.join(folder_path, os.path.basename(file_path))
            )

            logging.info(f"Uploaded {file_path} to {folder_path}")
            return True
        except Exception as e:
            logging.error(f"Error uploading {file_path}: {str(e)}")
            return False
