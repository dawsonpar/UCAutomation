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
        self.processed_files = self._load_processed_files()

    def _load_processed_files(self):
        if os.path.exists(self.processed_files_path):
            with open(self.processed_files_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _save_processed_files(self):
        with open(self.processed_files_path, "w") as f:
            json.dump(self.processed_files, f)

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

    def download_file(self, file_id, destination_path):
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        with open(destination_path, "wb") as f:
            f.write(fh.read())

    def upload_file(self, file_path, file_name, parent_folder_id):
        file_metadata = {"name": file_name, "parents": [parent_folder_id]}
        media = MediaFileUpload(file_path, resumable=True)
        request = self.service.files().create(
            body=file_metadata, media_body=media, fields="id"
        )
        response = None
        while response is None:
            status, response = request.next_chunk()

    def is_processed(self, file_id, modified_time):
        return self.processed_files.get(file_id) == modified_time

    def mark_as_processed(self, file_id, modified_time):
        self.processed_files[file_id] = modified_time
        self._save_processed_files()
