import io
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class GoogleDriveService:
    def __init__(self, folder_id, processed_files_path="processed_files.json"):
        credentials_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
        if not credentials_path:
            raise ValueError("GOOGLE_CREDENTIALS_PATH environment variable not set.")
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/drive"]
        )
        self.service = build("drive", "v3", credentials=self.credentials)
        self.folder_id = folder_id
        self.processed_files_path = processed_files_path

    def list_files(self):
        results = (
            self.service.files()
            .list(
                q=f"'{self.folder_id}' in parents",
                fields="files(id, name, modifiedTime)",
            )
            .execute()
        )
        files = results.get("files", [])
        return files
