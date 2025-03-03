import os
from unittest.mock import MagicMock, patch

import pytest

from google_drive_service import GoogleDriveService


def test_list_files():
    folder_id = "test_folder_id"
    mock_credentials = MagicMock()
    mock_service = MagicMock()
    mock_files = [
        {"id": "1", "name": "test_file.txt", "modifiedTime": "2025-03-03T12:00:00Z"}
    ]

    with patch(
        "google_drive_service.service_account.Credentials.from_service_account_file",
        return_value=mock_credentials,
    ), patch("google_drive_service.build", return_value=mock_service):

        google_drive_service = GoogleDriveService(folder_id)

        mock_service.files.return_value.list.return_value.execute.return_value = {
            "files": mock_files
        }

        files = google_drive_service.list_files()

        assert files == mock_files
        mock_service.files.return_value.list.assert_called_once_with(
            q=f"'{folder_id}' in parents", fields="files(id, name, modifiedTime)"
        )
