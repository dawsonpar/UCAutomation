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

    def list_files(self, folder_id=None, depth=0):
        if folder_id is None:
            folder_id = self.folder_id

        results = (
            self.service.files()
            .list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, mimeType)",
            )
            .execute()
        )

        files = results.get("files", [])
        all_files = []

        for file in files:
            indent = "  " * depth
            print(f"{indent}- {file['name']} (ID: {file['id']})")

            all_files.append(file)

            # Check if the file is a folder, then recurse
            if file["mimeType"] == "application/vnd.google-apps.folder":
                all_files.extend(self.list_files(file["id"], depth + 1))

        return all_files

    def download_file(self, file_id, destination):
        request = self.service.files().get_media(fileId=file_id)

        os.makedirs(os.path.dirname(destination), exist_ok=True)

        with open(destination, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

        return os.path.exists(destination)
