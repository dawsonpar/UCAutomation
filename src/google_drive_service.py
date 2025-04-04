import logging
import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from firestore_service import FirestoreService

# Configure logging
log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class GoogleDriveService:
    def __init__(
        self,
        folder_id,
        credentials_path=None,
        firebase_credentials_path=None,
        collection_name="processed_files",
    ):
        load_dotenv()
        credentials_path = credentials_path or os.environ.get("GOOGLE_CREDENTIALS_PATH")
        if not credentials_path:
            raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable not set.")

        # Verify credentials file exists
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Google Drive credentials file not found at {credentials_path}"
            )

        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)
        self.folder_id = folder_id

        # Initialize Firestore service for tracking processed files
        self.firestore_service = FirestoreService(
            collection_name=collection_name, credentials_path=firebase_credentials_path
        )

    def list_files(self, folder_id=None, depth=0):
        if folder_id is None:
            folder_id = self.folder_id

        try:
            results = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents",
                    fields="files(id, name, mimeType)",
                )
                .execute()
            )
        except Exception as e:
            logging.error(f"Error listing files in folder {folder_id}: {str(e)}")
            return []

        files = results.get("files", [])
        all_files = []

        for file in files:
            indent = "  " * depth
            logging.info(f"{indent}- {file['name']} (ID: {file['id']})")

            all_files.append(file)

            # Check if the file is a folder, then recurse
            if file["mimeType"] == "application/vnd.google-apps.folder":
                all_files.extend(self.list_files(file["id"], depth + 1))

        return all_files

    def download_file(self, file_id, destination):
        try:
            request = self.service.files().get_media(fileId=file_id)

            # Create destination directory if it doesn't exist
            os.makedirs(os.path.dirname(destination), exist_ok=True)

            with open(destination, "wb") as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()

            return os.path.exists(destination)
        except Exception as e:
            logging.error(f"Error downloading file {file_id}: {str(e)}")
            return False

    def upload_file(self, file_path, folder_id=None):
        """Uploads a file to Google Drive inside the specified folder."""
        if folder_id is None:
            folder_id = self.folder_id

        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return None

        try:
            file_metadata = {
                "name": os.path.basename(file_path),
                "parents": [folder_id],
            }

            media = MediaFileUpload(file_path, resumable=True)

            file = (
                self.service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )

            logging.info(
                f"Uploaded {file_path} to Google Drive with ID: {file.get('id')}"
            )
            return file.get("id")
        except Exception as e:
            logging.error(f"Error uploading file {file_path}: {str(e)}")
            return None

    def is_file_processed(self, file_id):
        """Check if a file has already been processed using Firestore."""
        return self.firestore_service.is_processed(file_id)

    def mark_file_as_processing(self, file_id, machine_id=None):
        """Mark a file as currently being processed in Firestore."""
        return self.firestore_service.mark_as_processing(file_id, machine_id)

    def mark_file_as_processed(self, file_id, machine_id=None, additional_data=None):
        """Mark a file as successfully processed in Firestore."""
        return self.firestore_service.mark_as_processed(
            file_id, machine_id, additional_data
        )

    def get_file_status(self, file_id):
        """Get the processing status of a file from Firestore."""
        return self.firestore_service.get_file_status(file_id)
