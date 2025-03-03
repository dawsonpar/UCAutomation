import os
from unittest.mock import MagicMock, patch

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
