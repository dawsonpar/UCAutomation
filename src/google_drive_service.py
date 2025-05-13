import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from firestore_service import FirestoreService
from log_config import get_logger

logger = get_logger()


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

    def get_storage_quota(self):
        """Retrieves storage quota information for the service account.

        Returns:
            dict: A dictionary containing the following quota information:
                - limit: Total quota in bytes
                - usage: Current usage in bytes
                - usage_in_drive: Usage in Drive in bytes
                - usage_in_drive_trash: Usage in Drive trash in bytes
                - usage_percentage: Percentage of quota used (0-100)
                - remaining: Remaining quota in bytes
                - remaining_readable: Remaining quota in human-readable format
            None: If an error occurred
        """
        try:
            about = self.service.about().get(fields="storageQuota").execute()
            storage_quota = about.get("storageQuota", {})

            # Extract quota information
            limit = int(storage_quota.get("limit", 0))
            usage = int(storage_quota.get("usage", 0))
            usage_in_drive = int(storage_quota.get("usageInDrive", 0))
            usage_in_drive_trash = int(storage_quota.get("usageInDriveTrash", 0))

            # Calculate percentage and remaining
            usage_percentage = (usage / limit * 100) if limit > 0 else 0
            remaining = limit - usage

            # Convert remaining bytes to human-readable format
            units = ["B", "KB", "MB", "GB", "TB"]
            remaining_readable = ""
            if remaining > 0:
                i = 0
                remaining_size = float(remaining)
                while remaining_size >= 1024 and i < len(units) - 1:
                    remaining_size /= 1024
                    i += 1
                remaining_readable = f"{remaining_size:.2f} {units[i]}"

            # Log quota information
            logger.info(
                f"Drive storage quota: {usage / (1024 * 1024 * 1024):.2f} GB used out of {limit / (1024 * 1024 * 1024):.2f} GB"
            )

            return {
                "limit": limit,
                "usage": usage,
                "usage_in_drive": usage_in_drive,
                "usage_in_drive_trash": usage_in_drive_trash,
                "usage_percentage": usage_percentage,
                "remaining": remaining,
                "remaining_readable": remaining_readable,
            }

        except Exception as e:
            logger.error(f"Error getting Drive storage quota: {str(e)}")
            return None

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
            logger.error(f"Error listing files in folder {folder_id}: {str(e)}")
            return []

        files = results.get("files", [])
        all_files = []

        for file in files:
            indent = "  " * depth
            logger.info(f"{indent}- {file['name']} (ID: {file['id']})")

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
            logger.error(f"Error downloading file {file_id}: {str(e)}")
            return False

    def upload_file(self, file_path, folder_id=None):
        """Uploads a file to Google Drive inside the specified folder."""
        if folder_id is None:
            folder_id = self.folder_id

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
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

            logger.info(
                f"Uploaded {file_path} to Google Drive with ID: {file.get('id')}"
            )
            return file.get("id")
        except Exception as e:
            logger.error(f"Error uploading file {file_path}: {str(e)}")
            return None

    def move_file(self, file_id, folder_id):
        """
        Move the specified file to the specified folder in Google Drive.

        Args:
            file_id (str): The ID of the file to move.
            folder_id (str): The ID of the destination folder.

        Returns:
            list: The new parent folder IDs if successful, None otherwise.
        """

        try:
            file = self.service.files().get(fileId=file_id, fields="parents").execute()
            previous_parents = ",".join(file.get("parents"))

            file = (
                self.service.files()
                .update(
                    fileId=file_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields="id, parents",
                )
                .execute()
            )
            logger.info(f"File {file_id} moved to {file.get("parents")}.")
            return file.get("parents")
        except Exception as e:
            logger.error(f"Error moving file {file_id}: {str(e)}")
            return None

    def is_file_processed(self, file_id):
        """Check if a file has already been processed using Firestore."""
        return self.firestore_service.is_processed(file_id)

    def is_file_uploaded(self, file_id):
        """Check if a file has already been uploaded using Firestore."""
        return self.firestore_service.is_uploaded(file_id)

    def mark_file_as_processing(self, file_id, machine_id=None):
        """Mark a file as currently being processed in Firestore."""
        return self.firestore_service.mark_as_processing(file_id, machine_id)

    def mark_file_as_processed(self, file_id, machine_id=None, additional_data=None):
        """Mark a file as successfully processed in Firestore."""
        return self.firestore_service.mark_as_processed(
            file_id, machine_id, additional_data
        )

    def mark_file_as_uploaded(self, file_id, machine_id=None, additional_data=None):
        """Mark a file as successfully uploaded in Firestore."""
        return self.firestore_service.mark_as_uploaded(
            file_id, machine_id, additional_data
        )

    def mark_file_as_failed(self, file_id, machine_id=None, error_message=None):
        """Mark a file as failed processing in Firestore."""
        return self.firestore_service.mark_as_failed(file_id, machine_id, error_message)

    def get_file_status(self, file_id):
        """Get the processing status of a file from Firestore."""
        return self.firestore_service.get_file_status(file_id)
