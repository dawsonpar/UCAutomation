import os
from unittest.mock import MagicMock, mock_open, patch

import pytest
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from google_drive_service import GoogleDriveService


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
    ), patch("google_drive_service.build", return_value=mock_service):

        google_drive_service = GoogleDriveService(folder_id)

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
    ) as mock_exists:

        google_drive_service = GoogleDriveService(folder_id)

        # Mock API request and download behavior
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
        "builtins.open", mock_open()
    ), patch(
        "os.makedirs"
    ), patch(
        "os.path.exists", return_value=False
    ):

        google_drive_service = GoogleDriveService(folder_id)

        mock_service.files.return_value.get_media.side_effect = Exception(
            "File not found"
        )

        with pytest.raises(Exception, match="File not found"):
            google_drive_service.download_file(file_id, destination)


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
    ) as mock_media_file_upload:

        google_drive_service = GoogleDriveService(folder_id)

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
    ) as mock_media_file_upload:

        google_drive_service = GoogleDriveService(folder_id)

        mock_media = MagicMock()
        mock_media_file_upload.return_value = mock_media

        mock_service.files.return_value.create.return_value.execute.side_effect = (
            HttpError(resp=MagicMock(status=403), content=b"Permission denied")
        )

        with pytest.raises(HttpError, match="Permission denied"):
            google_drive_service.upload_file(file_path, folder_id)

        mock_service.files.return_value.create.assert_called_once_with(
            body={"name": os.path.basename(file_path), "parents": [folder_id]},
            media_body=mock_media,
            fields="id",
        )
