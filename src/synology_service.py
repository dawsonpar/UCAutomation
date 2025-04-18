import os
import shutil

from firestore_service import FirestoreService
from log_config import get_logger

logger = get_logger()


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
            logger.error(f"File not found: {file_path}")
            return None

        try:
            # Create the destination folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)

            # Upload the file
            shutil.copy2(
                file_path, os.path.join(folder_path, os.path.basename(file_path))
            )

            logger.info(f"Uploaded {file_path} to {folder_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {str(e)}")
            return False
