import logging
import os
import sys
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Add the src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import utils
from google_drive_service import GoogleDriveService


@pytest.fixture
def mock_quota_info():
    """Return sample quota information for testing"""
    return {
        "limit": 15 * 1024 * 1024 * 1024,  # 15 GB
        "usage": 8 * 1024 * 1024 * 1024,  # 8 GB
        "usage_percentage": 53.33,
        "usage_in_drive": 7 * 1024 * 1024 * 1024,  # 7 GB
        "usage_in_drive_trash": 1 * 1024 * 1024 * 1024,  # 1 GB
        "remaining": 7 * 1024 * 1024 * 1024,  # 7 GB
    }


@pytest.fixture
def mock_quota_info_high():
    """Return sample quota information with high usage for testing"""
    return {
        "limit": 15 * 1024 * 1024 * 1024,  # 15 GB
        "usage": 14 * 1024 * 1024 * 1024,  # 14 GB
        "usage_percentage": 93.33,
        "usage_in_drive": 13 * 1024 * 1024 * 1024,  # 13 GB
        "usage_in_drive_trash": 1 * 1024 * 1024 * 1024,  # 1 GB
        "remaining": 1 * 1024 * 1024 * 1024,  # 1 GB
    }


@pytest.fixture
def mock_drive_service():
    """Return a mock Google Drive service for testing"""
    mock_service = MagicMock(spec=GoogleDriveService)
    mock_service.get_storage_quota.return_value = {
        "limit": 15 * 1024 * 1024 * 1024,  # 15 GB
        "usage": 8 * 1024 * 1024 * 1024,  # 8 GB
        "usage_percentage": 53.33,
        "usage_in_drive": 7 * 1024 * 1024 * 1024,  # 7 GB
        "usage_in_drive_trash": 1 * 1024 * 1024 * 1024,  # 1 GB
        "remaining": 7 * 1024 * 1024 * 1024,  # 7 GB
    }
    return mock_service


class TestFormatSize:
    """Tests for format_size function"""

    def test_format_size_zero(self):
        """Test formatting zero bytes"""
        result = utils.format_size(0)
        assert result == "0 B"

    def test_format_size_bytes(self):
        """Test formatting values in bytes"""
        result = utils.format_size(500)
        assert result == "500.00 B"

    def test_format_size_kb(self):
        """Test formatting values in kilobytes"""
        result = utils.format_size(1500)
        assert result == "1.46 KB"

    def test_format_size_mb(self):
        """Test formatting values in megabytes"""
        result = utils.format_size(1500000)
        assert result == "1.43 MB"

    def test_format_size_gb(self):
        """Test formatting values in gigabytes"""
        result = utils.format_size(1500000000)
        assert result == "1.40 GB"

    def test_format_size_tb(self):
        """Test formatting values in terabytes"""
        result = utils.format_size(1500000000000)
        assert result == "1.36 TB"


class TestGetQuota:
    """Tests for get_quota function"""

    @patch.dict(
        os.environ,
        {
            "INGEST_FOLDER_ID": "test_folder_id",
            "GOOGLE_CREDENTIALS_PATH": "/path/to/google_creds.json",
            "FIREBASE_CREDENTIALS_PATH": "/path/to/firebase_creds.json",
        },
    )
    @patch("utils.GoogleDriveService")
    @patch("utils.load_dotenv")
    @patch("utils.print")
    def test_get_quota_success(
        self, mock_print, mock_load_dotenv, mock_drive_service_cls, mock_quota_info
    ):
        """Test successful quota retrieval"""
        # Setup mock
        mock_drive_service_instance = mock_drive_service_cls.return_value
        mock_drive_service_instance.get_storage_quota.return_value = mock_quota_info

        # Call function
        result = utils.get_quota()

        # Verify
        mock_load_dotenv.assert_called_once()
        mock_drive_service_cls.assert_called_once_with(
            folder_id="test_folder_id",
            credentials_path="/path/to/google_creds.json",
            firebase_credentials_path="/path/to/firebase_creds.json",
        )
        mock_drive_service_instance.get_storage_quota.assert_called_once()
        assert result == mock_quota_info
        assert mock_print.call_count > 5  # Multiple print statements

    @patch.dict(os.environ, {}, clear=True)
    @patch("utils.load_dotenv")
    @patch("utils.print")
    @patch("utils.sys.exit")
    def test_get_quota_missing_env_vars(self, mock_exit, mock_print, mock_load_dotenv):
        """Test handling missing environment variables"""
        # Call function
        result = utils.get_quota()

        # Verify
        mock_load_dotenv.assert_called_once()
        mock_print.assert_called_once()
        mock_exit.assert_not_called()
        assert result is None

    @patch.dict(
        os.environ,
        {
            "INGEST_FOLDER_ID": "test_folder_id",
            "GOOGLE_CREDENTIALS_PATH": "/path/to/google_creds.json",
            "FIREBASE_CREDENTIALS_PATH": "/path/to/firebase_creds.json",
        },
    )
    @patch("utils.GoogleDriveService")
    @patch("utils.load_dotenv")
    @patch("utils.print")
    @patch("utils.sys.exit")
    def test_get_quota_no_info(
        self, mock_exit, mock_print, mock_load_dotenv, mock_drive_service_cls
    ):
        """Test handling case when no quota info is returned"""
        # Setup mock
        mock_drive_service_instance = mock_drive_service_cls.return_value
        mock_drive_service_instance.get_storage_quota.return_value = None

        # Call function
        result = utils.get_quota()

        # Verify
        mock_exit.assert_not_called()
        assert result is None
        mock_print.assert_any_call(
            "Error: Failed to retrieve storage quota information."
        )

    @patch.dict(
        os.environ,
        {
            "INGEST_FOLDER_ID": "test_folder_id",
            "GOOGLE_CREDENTIALS_PATH": "/path/to/google_creds.json",
            "FIREBASE_CREDENTIALS_PATH": "/path/to/firebase_creds.json",
        },
    )
    @patch("utils.GoogleDriveService")
    @patch("utils.load_dotenv")
    @patch("utils.print")
    def test_get_quota_high_usage(
        self, mock_print, mock_load_dotenv, mock_drive_service_cls, mock_quota_info_high
    ):
        """Test handling high quota usage"""
        # Setup mock
        mock_drive_service_instance = mock_drive_service_cls.return_value
        mock_drive_service_instance.get_storage_quota.return_value = (
            mock_quota_info_high
        )

        # Call function
        result = utils.get_quota()

        # Verify
        assert result == mock_quota_info_high
        assert (
            mock_print.call_count >= 10
        )  # At least 10 print calls with the additional warnings

    @patch.dict(
        os.environ,
        {
            "INGEST_FOLDER_ID": "test_folder_id",
            "GOOGLE_CREDENTIALS_PATH": "/path/to/google_creds.json",
            "FIREBASE_CREDENTIALS_PATH": "/path/to/firebase_creds.json",
        },
    )
    @patch("utils.GoogleDriveService")
    @patch("utils.load_dotenv")
    @patch("utils.print")
    @patch("utils.sys.exit")
    def test_get_quota_exception(
        self, mock_exit, mock_print, mock_load_dotenv, mock_drive_service_cls
    ):
        """Test handling exceptions"""
        # Setup mock
        mock_drive_service_instance = mock_drive_service_cls.return_value
        mock_drive_service_instance.get_storage_quota.side_effect = Exception(
            "Test error"
        )

        # Call function
        result = utils.get_quota()

        # Verify
        mock_print.assert_called_with("Error: Test error")
        mock_exit.assert_not_called()
        assert result is None


class TestGetQuotaThreshold:
    """Tests for get_quota_threshold function"""

    @patch("utils.logging.info")
    def test_get_quota_threshold_none(self, mock_logging_info):
        """Test handling None quota info"""
        result = utils.get_quota_threshold(None)
        assert result is False
        assert mock_logging_info.call_count == 0

    @patch("utils.logging.info")
    @patch("utils.logging.error")
    @patch("utils.logging.warning")
    def test_get_quota_threshold_below(
        self,
        mock_logging_warning,
        mock_logging_error,
        mock_logging_info,
        mock_quota_info,
    ):
        """Test handling quota usage below threshold"""
        result = utils.get_quota_threshold(mock_quota_info, threshold=70.0)
        assert result is True
        mock_logging_info.assert_called_once()
        mock_logging_error.assert_not_called()
        mock_logging_warning.assert_not_called()

    @patch("utils.logging.info")
    @patch("utils.logging.error")
    @patch("utils.logging.warning")
    def test_get_quota_threshold_above(
        self,
        mock_logging_warning,
        mock_logging_error,
        mock_logging_info,
        mock_quota_info_high,
    ):
        """Test handling quota usage above threshold"""
        result = utils.get_quota_threshold(mock_quota_info_high, threshold=90.0)
        assert result is False
        mock_logging_info.assert_called_once()
        mock_logging_error.assert_called_once()
        mock_logging_warning.assert_called_once()

    @patch("utils.logging.info")
    @patch("utils.logging.error")
    @patch("utils.logging.warning")
    def test_get_quota_threshold_equal(
        self, mock_logging_warning, mock_logging_error, mock_logging_info
    ):
        """Test handling quota usage equal to threshold"""
        quota_info = {
            "limit": 10 * 1024 * 1024 * 1024,
            "usage": 9 * 1024 * 1024 * 1024,
            "usage_percentage": 90.0,
        }
        result = utils.get_quota_threshold(quota_info, threshold=90.0)
        assert result is True
        mock_logging_info.assert_called_once()
        mock_logging_error.assert_not_called()
        mock_logging_warning.assert_not_called()


class TestProcessFile:
    """Tests for process_file function"""

    def test_process_file_already_processed(self, mock_drive_service):
        """Test handling already processed file"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = True
        mock_converter = MagicMock()
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is True
        mock_drive_service.is_file_processed.assert_called_once_with("file123")
        mock_converter.convert.assert_not_called()
        mock_drive_service.download_file.assert_not_called()

    def test_process_file_max_retries_exceeded(self, mock_drive_service):
        """Test handling file with max retries exceeded"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = {
            "status": "failed",
            "retry_count": 3,
        }
        mock_converter = MagicMock()
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_drive_service.is_file_processed.assert_called_once_with("file123")
        mock_drive_service.get_file_status.assert_called_once_with("file123")
        mock_converter.convert.assert_not_called()
        mock_drive_service.download_file.assert_not_called()

    def test_process_file_already_processing(self, mock_drive_service):
        """Test handling file already being processed by another machine"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = {
            "status": "processing",
            "retry_count": 0,
        }
        mock_drive_service.mark_file_as_processing.return_value = False
        mock_converter = MagicMock()
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_drive_service.is_file_processed.assert_called_once_with("file123")
        mock_drive_service.mark_file_as_processing.assert_called_once_with(
            "file123", "test-machine"
        )
        mock_converter.convert.assert_not_called()

    def test_process_file_download_failure(self, mock_drive_service):
        """Test handling file download failure"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = None
        mock_drive_service.mark_file_as_processing.return_value = True
        mock_drive_service.download_file.return_value = False
        mock_converter = MagicMock()
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_drive_service.download_file.assert_called_once_with(
            "file123", "/tmp/download/test.cr3"
        )
        mock_drive_service.mark_file_as_failed.assert_called_once()
        mock_converter.convert.assert_not_called()

    def test_process_file_conversion_failure(self, mock_drive_service):
        """Test handling file conversion failure"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = None
        mock_drive_service.mark_file_as_processing.return_value = True
        mock_drive_service.download_file.return_value = True
        mock_converter = MagicMock()
        mock_converter.convert.return_value = False
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_converter.convert.assert_called_once_with(
            "/tmp/download/test.cr3", "/tmp/output", "file123", already_marked=True
        )
        mock_drive_service.mark_file_as_failed.assert_called_once()
        mock_drive_service.upload_file.assert_not_called()

    def test_process_file_upload_failure(self, mock_drive_service):
        """Test handling file upload failure"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = None
        mock_drive_service.mark_file_as_processing.return_value = True
        mock_drive_service.download_file.return_value = True
        mock_drive_service.upload_file.return_value = None
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_drive_service.upload_file.assert_called_once_with(
            "/tmp/output/test.dng", "dng_folder_id"
        )
        mock_drive_service.mark_file_as_failed.assert_called_once()
        mock_drive_service.mark_file_as_processed.assert_not_called()

    def test_process_file_success(self, mock_drive_service):
        """Test successful file processing"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = None
        mock_drive_service.mark_file_as_processing.return_value = True
        mock_drive_service.download_file.return_value = True
        mock_drive_service.upload_file.return_value = "uploaded_dng_id"
        mock_converter = MagicMock()
        mock_converter.convert.return_value = True
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is True
        mock_drive_service.mark_file_as_processed.assert_called_once_with(
            "file123",
            "test-machine",
            {
                "original_filename": "test.cr3",
                "converted_filename": "test.dng",
                "dng_file_id": "uploaded_dng_id",
            },
        )

    def test_process_file_exception(self, mock_drive_service):
        """Test handling unexpected exceptions during processing"""
        # Setup mocks
        mock_drive_service.is_file_processed.return_value = False
        mock_drive_service.get_file_status.return_value = None
        mock_drive_service.mark_file_as_processing.return_value = True
        mock_drive_service.download_file.return_value = True
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("Test error")
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.process_file(
            mock_drive_service,
            mock_converter,
            test_file,
            "test-machine",
            "/tmp/download",
            "/tmp/output",
            "dng_folder_id",
        )

        # Verify
        assert result is False
        mock_drive_service.mark_file_as_failed.assert_called_once()
        assert (
            "Test error"
            in mock_drive_service.mark_file_as_failed.call_args[1]["error_message"]
        )
