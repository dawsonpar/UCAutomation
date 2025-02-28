import json
import os
from unittest.mock import Mock, patch

import pytest

from google_drive_service import GoogleDriveService


@pytest.fixture
def mock_service():
    mock = Mock()
    mock.files.return_value = mock
    return mock


@pytest.fixture
def google_drive_service(mock_service, tmp_path):
    with patch("googleapiclient.discovery.build", return_value=mock_service):
        processed_files_path = str(tmp_path / "test_processed_files.json")
        service = GoogleDriveService("test_folder_id", processed_files_path)
        return service, mock_service, processed_files_path


def test_list_files(google_drive_service):
    service, mock_service, _ = google_drive_service
    mock_service.files().list().execute.return_value = {
        "files": [{"id": "1", "name": "file1.txt", "modifiedTime": "time1"}]
    }
    files = service.list_files()
    assert files == [{"id": "1", "name": "file1.txt", "modifiedTime": "time1"}]


def test_download_file(google_drive_service, tmp_path):
    service, mock_service, _ = google_drive_service
    mock_media = Mock()
    mock_service.files().get_media.return_value = mock_media
    mock_media.next_chunk.return_value = ((Mock(), True),)
    destination_path = str(tmp_path / "downloaded_file.txt")
    service.download_file("file_id", destination_path)
    mock_service.files().get_media.assert_called_once_with(fileId="file_id")
    assert os.path.exists(destination_path)


def test_upload_file(google_drive_service, tmp_path):
    service, mock_service, _ = google_drive_service
    test_file_path = tmp_path / "test_file.txt"
    test_file_path.write_text("test content")
    mock_service.files().create().next_chunk.return_value = (
        (Mock(), None),
        (Mock(), "done"),
    )
    service.upload_file(str(test_file_path), "test_file.txt", "test_parent_id")
    mock_service.files().create.assert_called_once()


def test_is_processed_and_mark_as_processed(google_drive_service, tmp_path):
    service, _, processed_files_path = google_drive_service
    file_id = "test_file_id"
    modified_time = "test_modified_time"

    assert not service.is_processed(file_id, modified_time)
    service.mark_as_processed(file_id, modified_time)
    assert service.is_processed(file_id, modified_time)

    # Verify the processed_files.json file was updated
    with open(processed_files_path, "r") as f:
        data = json.load(f)
        assert data[file_id] == modified_time


def test_load_and_save_processed_files(google_drive_service, tmp_path):
    service, _, processed_files_path = google_drive_service
    file_id = "test_file_id"
    modified_time = "test_modified_time"

    service.mark_as_processed(file_id, modified_time)

    # Create a new service instance to simulate loading from file
    with patch("googleapiclient.discovery.build", return_value=mock_service):
        new_service = GoogleDriveService("test_folder_id", processed_files_path)
    assert new_service.is_processed(file_id, modified_time)
