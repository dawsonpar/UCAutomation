import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from google_drive_service import GoogleDriveService


@pytest.fixture
def mock_firestore_service():
    with patch("google_drive_service.FirestoreService") as mock_firestore_cls:
        mock_firestore = MagicMock()
        mock_firestore_cls.return_value = mock_firestore
        yield mock_firestore


def test_list_files():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()
    mock_files = [
        {
            "id": "1",
            "name": "folder_1",
            "mimeType": "application/vnd.google-apps.folder",
        },
        {"id": "2", "name": "file_1.txt", "mimeType": "text/plain"},
    ]
    subfolder_files = [{"id": "3", "name": "file_2.txt", "mimeType": "text/plain"}]

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "os.path.exists", return_value=True
    ), patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        mock_service.files.return_value.list.return_value.execute.side_effect = [
            {"files": mock_files},
            {"files": subfolder_files},
        ]

        files = google_drive_service.list_files()

        expected_files = [
            {
                "id": "1",
                "name": "folder_1",
                "mimeType": "application/vnd.google-apps.folder",
            },
            {
                "id": "3",
                "name": "file_2.txt",
                "mimeType": "text/plain",
            },
            {"id": "2", "name": "file_1.txt", "mimeType": "text/plain"},
        ]

        assert files == expected_files
        mock_service.files.return_value.list.assert_any_call(
            q=f"'{folder_id}' in parents", fields="files(id, name, mimeType)"
        )


def test_list_files_error():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "os.path.exists", return_value=True
    ), patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        # Simulate an API error
        mock_service.files.return_value.list.return_value.execute.side_effect = (
            Exception("API Error")
        )

        files = google_drive_service.list_files()

        # Should return empty list on error
        assert files == []


def test_download_file():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()

    file_id = "test_file_id"
    destination = "downloads/test_file.txt"

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "builtins.open", mock_open()
    ) as mock_file, patch(
        "os.makedirs"
    ) as mock_makedirs, patch(
        "os.path.exists", return_value=True
    ) as mock_exists, patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        mock_request = MagicMock()
        mock_service.files.return_value.get_media.return_value = mock_request
        mock_downloader = MagicMock()
        mock_downloader.next_chunk.side_effect = [
            (None, False),
            (None, True),
        ]

        with patch(
            "google_drive_service.MediaIoBaseDownload", return_value=mock_downloader
        ):
            success = google_drive_service.download_file(file_id, destination)

        assert success is True
        mock_service.files.return_value.get_media.assert_called_once_with(
            fileId=file_id
        )


def test_download_file_failure():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()

    file_id = "invalid_file_id"
    destination = "downloads/invalid_file.txt"

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "os.path.exists", return_value=True
    ), patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        mock_service.files.return_value.get_media.side_effect = Exception(
            "File not found"
        )

        success = google_drive_service.download_file(file_id, destination)

        assert success is False


def test_upload_file():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()

    file_path = "test_file.txt"
    file_id = "uploaded_file_id"

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "google_drive_service.MediaFileUpload"
    ) as mock_media_file_upload, patch(
        "os.path.exists", return_value=True
    ), patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        mock_media = MagicMock()
        mock_media_file_upload.return_value = mock_media

        mock_service.files.return_value.create.return_value.execute.return_value = {
            "id": file_id
        }

        uploaded_file_id = google_drive_service.upload_file(file_path, folder_id)

        assert uploaded_file_id == file_id
        mock_service.files.return_value.create.assert_called_once_with(
            body={"name": os.path.basename(file_path), "parents": [folder_id]},
            media_body=mock_media,
            fields="id",
        )


def test_upload_file_failure():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()

    file_path = "test_file.txt"

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service), patch(
        "google_drive_service.MediaFileUpload"
    ) as mock_media_file_upload, patch(
        "os.path.exists", return_value=True
    ), patch(
        "google_drive_service.FirestoreService"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        mock_media = MagicMock()
        mock_media_file_upload.return_value = mock_media

        mock_service.files.return_value.create.return_value.execute.side_effect = (
            Exception("Upload error")
        )

        uploaded_file_id = google_drive_service.upload_file(file_path, folder_id)

        assert uploaded_file_id is None


def test_upload_nonexistent_file():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()

    file_path = "nonexistent_file.txt"

    # Use a side_effect function to return True for credential path and False for the upload file
    def path_exists_side_effect(path):
        if path == "mock/path.json":
            return True
        return False

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build"), patch(
        "os.path.exists", side_effect=path_exists_side_effect
    ), patch(
        "google_drive_service.FirestoreService"
    ), patch(
        "google_drive_service.load_dotenv"
    ):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        uploaded_file_id = google_drive_service.upload_file(file_path, folder_id)

        assert uploaded_file_id is None


def test_file_status_methods(mock_firestore_service):
    folder_id = "test_folder_id"
    file_id = "test_file_id"

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file"
    ), patch("google_drive_service.build"), patch("os.path.exists", return_value=True):

        google_drive_service = GoogleDriveService(
            folder_id, credentials_path="mock/path.json"
        )

        # Test is_file_processed
        mock_firestore_service.is_processed.return_value = True
        result = google_drive_service.is_file_processed(file_id)
        assert result is True
        mock_firestore_service.is_processed.assert_called_with(file_id)

        # Test mark_file_as_processing
        mock_firestore_service.mark_as_processing.return_value = True
        result = google_drive_service.mark_file_as_processing(file_id, "test-machine")
        assert result is True
        mock_firestore_service.mark_as_processing.assert_called_with(
            file_id, "test-machine"
        )

        # Test mark_file_as_processed
        mock_firestore_service.mark_as_processed.return_value = True
        data = {"filename": "test.dng"}
        result = google_drive_service.mark_file_as_processed(
            file_id, "test-machine", data
        )
        assert result is True
        mock_firestore_service.mark_as_processed.assert_called_with(
            file_id, "test-machine", data
        )

        # Test mark_file_as_failed
        mock_firestore_service.mark_as_failed.return_value = True
        result = google_drive_service.mark_file_as_failed(
            file_id, "test-machine", "Conversion error"
        )
        assert result is True
        mock_firestore_service.mark_as_failed.assert_called_with(
            file_id, "test-machine", "Conversion error"
        )

        # Test get_file_status
        mock_firestore_service.get_file_status.return_value = {"status": "processed"}
        result = google_drive_service.get_file_status(file_id)
        assert result == {"status": "processed"}
        mock_firestore_service.get_file_status.assert_called_with(file_id)
