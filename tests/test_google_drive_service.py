import os
from unittest.mock import MagicMock, mock_open, patch

import pytest

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

        assert files == expected_files, f"Expected {expected_files}, but got {files}"

        mock_service.files.return_value.list.assert_any_call(
            q=f"'{folder_id}' in parents", fields="files(id, name, mimeType)"
        )
        mock_service.files.return_value.list.assert_any_call(
            q=f"'1' in parents", fields="files(id, name, mimeType)"
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

        # Assertions
        assert success is True
        mock_service.files.return_value.get_media.assert_called_once_with(
            fileId=file_id
        )
        mock_makedirs.assert_called_once_with(
            os.path.dirname(destination), exist_ok=True
        )
        mock_file.assert_called_once_with(destination, "wb")
        mock_downloader.next_chunk.assert_called()


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

        # Simulate API failure (e.g., file not found)
        mock_service.files.return_value.get_media.side_effect = Exception(
            "File not found"
        )

        with pytest.raises(Exception, match="File not found"):
            google_drive_service.download_file(file_id, destination)
