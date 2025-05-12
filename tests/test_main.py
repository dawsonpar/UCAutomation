import os
from unittest.mock import MagicMock, patch

import pytest

from utils import process_file

# Define MAX_RETRIES to match the value in utils.py process_file function
MAX_RETRIES = 3


@pytest.fixture
def mock_services():
    """Setup mock services for testing process_file function"""
    drive_service = MagicMock()
    converter = MagicMock()
    machine_id = "test-machine"
    download_dir = "/test/download/dir"
    output_dir = "/test/output/dir"
    dng_folder_id = "dng_folder_id_123"

    return {
        "drive_service": drive_service,
        "converter": converter,
        "machine_id": machine_id,
        "download_dir": download_dir,
        "output_dir": output_dir,
        "dng_folder_id": dng_folder_id,
    }


@pytest.fixture
def test_file():
    """Sample file data for testing"""
    return {
        "id": "file_id_123",
        "name": "test_photo.cr3",
    }


def test_process_file_already_processed(mock_services, test_file):
    """Test processing a file that's already been processed"""
    # Set up the mock to indicate file is already processed
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = True

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return True and not attempt further processing
    assert result is True
    mock_services["drive_service"].is_file_processed.assert_called_once_with(
        test_file["id"]
    )
    mock_services["drive_service"].mark_file_as_processing.assert_not_called()
    mock_services["drive_service"].download_file.assert_not_called()


def test_process_file_max_retries_exceeded(mock_services, test_file):
    """Test processing a file that has exceeded max retry attempts"""
    # Set up mocks
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False

    # Mock file status showing max retries exceeded
    mock_services["drive_service"].get_file_status.return_value = {
        "status": "failed",
        "retry_count": MAX_RETRIES,  # Equal to the max retry count
        "error_message": "Previous error",
    }

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and not attempt processing
    assert result is False
    mock_services["drive_service"].mark_file_as_processing.assert_not_called()
    mock_services["drive_service"].download_file.assert_not_called()


def test_process_file_download_failure(mock_services, test_file):
    """Test processing a file where download fails"""
    # Set up mocks
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = (
        None  # No existing status
    )
    mock_services["drive_service"].mark_file_as_processing.return_value = True

    # Make download fail
    mock_services["drive_service"].download_file.return_value = False

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and mark as failed
    assert result is False
    mock_services["drive_service"].download_file.assert_called_once()
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].mark_file_as_failed.assert_called_once()

    # Add debug print to see the call_args structure
    print(f"Call args: {mock_services['drive_service'].mark_file_as_failed.call_args}")
    print(f"Args: {mock_services['drive_service'].mark_file_as_failed.call_args[0]}")
    print(f"Kwargs: {mock_services['drive_service'].mark_file_as_failed.call_args[1]}")

    # Verify the error message contains "Failed to download"
    error_msg = mock_services["drive_service"].mark_file_as_failed.call_args[1][
        "error_message"
    ]
    assert "Failed to download" in error_msg

    # Shouldn't attempt conversion
    mock_services["converter"].convert.assert_not_called()


def test_process_file_conversion_failure(mock_services, test_file):
    """Test processing a file where conversion fails"""
    # Set up mocks for successful download but failed conversion
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = None
    mock_services["drive_service"].mark_file_as_processing.return_value = True
    mock_services["drive_service"].download_file.return_value = True

    # Make conversion fail
    mock_services["converter"].convert.return_value = False

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and mark as failed
    assert result is False
    mock_services["converter"].convert.assert_called_once()
    mock_services["drive_service"].mark_file_as_failed.assert_called_once()
    # Verify the error message contains "Failed to convert"
    error_msg = mock_services["drive_service"].mark_file_as_failed.call_args[1][
        "error_message"
    ]
    assert "Failed to convert" in error_msg

    # Shouldn't attempt upload
    mock_services["drive_service"].upload_file.assert_not_called()


def test_process_file_upload_failure(mock_services, test_file):
    """Test processing a file where upload to Google Drive fails"""
    # Set up mocks for successful download and conversion but failed upload
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = None
    mock_services["drive_service"].mark_file_as_processing.return_value = True
    mock_services["drive_service"].download_file.return_value = True
    mock_services["converter"].convert.return_value = True

    # Make upload fail
    mock_services["drive_service"].upload_file.return_value = None

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and mark as failed
    assert result is False
    mock_services["drive_service"].upload_file.assert_called_once()
    mock_services["drive_service"].mark_file_as_failed.assert_called_once()
    # Verify the error message contains "Failed to upload"
    error_msg = mock_services["drive_service"].mark_file_as_failed.call_args[1][
        "error_message"
    ]
    assert "Failed to upload" in error_msg

    # Shouldn't mark as processed
    mock_services["drive_service"].mark_file_as_processed.assert_not_called()


def test_process_file_exception_handling(mock_services, test_file):
    """Test handling exceptions during file processing"""
    # Set up mocks
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = None
    mock_services["drive_service"].mark_file_as_processing.return_value = True
    mock_services["drive_service"].download_file.return_value = True

    # Make conversion raise an exception
    mock_services["converter"].convert.side_effect = RuntimeError("Conversion error")

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and mark as failed
    assert result is False
    mock_services["drive_service"].mark_file_as_failed.assert_called_once()
    # Verify the error message contains the exception text
    error_msg = mock_services["drive_service"].mark_file_as_failed.call_args[1][
        "error_message"
    ]
    assert "Conversion error" in error_msg


def test_process_file_success(mock_services, test_file):
    """Test successful end-to-end processing of a file"""
    # Set up mocks for success at all stages
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = None
    mock_services["drive_service"].mark_file_as_processing.return_value = True
    mock_services["drive_service"].download_file.return_value = True
    mock_services["converter"].convert.return_value = True
    mock_services["drive_service"].upload_file.return_value = "uploaded_file_id_456"

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return True and follow the entire workflow
    assert result is True

    # Verify all steps were called in order
    mock_services["drive_service"].mark_file_as_processing.assert_called_once()
    mock_services["drive_service"].download_file.assert_called_once()
    mock_services["converter"].convert.assert_called_once()
    mock_services["drive_service"].upload_file.assert_called_once()

    # Verify correctly marked as processed with all metadata
    mock_services["drive_service"].mark_file_as_uploaded.assert_called_once()
    process_data = mock_services["drive_service"].mark_file_as_uploaded.call_args[0][2]
    assert process_data["original_filename"] == test_file["name"]
    assert process_data["converted_filename"] == "test_photo.dng"
    assert process_data["dng_file_id"] == "uploaded_file_id_456"


def test_process_file_already_being_processed(mock_services, test_file):
    """Test attempting to process a file already being processed by another machine"""
    # Set up mocks
    mock_services["drive_service"].is_file_uploaded.return_value = False
    mock_services["drive_service"].is_file_processed.return_value = False
    mock_services["drive_service"].get_file_status.return_value = None

    # Make mark_as_processing return False (already being processed)
    mock_services["drive_service"].mark_file_as_processing.return_value = False

    result = process_file(
        mock_services["drive_service"],
        mock_services["converter"],
        test_file,
        mock_services["machine_id"],
        mock_services["download_dir"],
        mock_services["output_dir"],
        mock_services["dng_folder_id"],
    )

    # Should return False and not proceed further
    assert result is False
    mock_services["drive_service"].download_file.assert_not_called()
    mock_services["converter"].convert.assert_not_called()
