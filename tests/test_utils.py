import logging
import os
import sys
import time
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

    @patch("utils.logger.info")
    def test_get_quota_threshold_none(self, mock_logging_info):
        """Test handling None quota info"""
        result = utils.get_quota_threshold(None)
        assert result is False
        assert mock_logging_info.call_count == 0

    @patch("utils.logger.info")
    @patch("utils.logger.error")
    @patch("utils.logger.warning")
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

    @patch("utils.logger.info")
    @patch("utils.logger.error")
    @patch("utils.logger.warning")
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

    @patch("utils.logger.info")
    @patch("utils.logger.error")
    @patch("utils.logger.warning")
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
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.is_file_uploaded.return_value = False
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

    def test_upload_file_success(self, mock_drive_service):
        """Test successful file processing"""
        # Setup mocks
        mock_drive_service.is_file_uploaded.return_value = False
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
        mock_drive_service.mark_file_as_uploaded.assert_called_once_with(
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
        mock_drive_service.is_file_uploaded.return_value = False
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


class TestCleanDownloadDirectories:
    """Tests for clean_download_directories function"""

    @patch("utils.os.path.expanduser")
    @patch("utils.os.path.exists")
    @patch("utils.os.path.isfile")
    @patch("utils.os.path.getmtime")
    @patch("utils.os.remove")
    @patch("utils.os.listdir")
    @patch("utils.time.time")
    @patch("utils.open", new_callable=mock_open)
    @patch("utils.logger")
    def test_files_deleted_past_cutoff(
        self,
        mock_logger,
        mock_open,
        mock_time,
        mock_listdir,
        mock_remove,
        mock_getmtime,
        mock_isfile,
        mock_exists,
        mock_expanduser,
    ):
        """Test files older than the cutoff time are correctly deleted"""
        # Setup mocks
        mock_expanduser.return_value = "/home/testuser"

        # Make sure .last_cleanup doesn't exist but directories do
        def exists_side_effect(path):
            if path == "/home/testuser/UCAutomation/.last_cleanup":
                return False
            return True

        mock_exists.side_effect = exists_side_effect

        # All paths are files for this test
        mock_isfile.return_value = True

        # Current time (e.g., 10 days since epoch)
        current_time = 10 * 24 * 60 * 60
        mock_time.return_value = current_time

        # Return different directories with test files
        def listdir_side_effect(path):
            if path == "/home/testuser/UCAutomation/downloads/raw_files":
                return ["old_file1.cr3", "recent_file.cr3"]
            elif path == "/home/testuser/UCAutomation/downloads/dng_files":
                return ["old_file2.dng"]
            return []

        mock_listdir.side_effect = listdir_side_effect

        # Set file modification times (8 days old and 2 days old)
        old_time = current_time - (8 * 24 * 60 * 60)  # 8 days old
        recent_time = current_time - (2 * 24 * 60 * 60)  # 2 days old

        def get_mtime(path):
            if "old_file" in path:
                return old_time
            return recent_time

        mock_getmtime.side_effect = get_mtime

        # Call function
        result = utils.clean_download_directories(
            base_dir="/home/testuser/UCAutomation"
        )

        # Verify results
        assert result == (1, 1)  # One raw file and one DNG file removed

        mock_remove.assert_any_call(
            "/home/testuser/UCAutomation/downloads/raw_files/old_file1.cr3"
        )
        mock_remove.assert_any_call(
            "/home/testuser/UCAutomation/downloads/dng_files/old_file2.dng"
        )
        assert mock_remove.call_count == 2

        # Verify the marker file was written with the current time
        mock_open.assert_called_with("/home/testuser/UCAutomation/.last_cleanup", "w")
        mock_open().write.assert_called_with(str(current_time))

        # Verify logging
        mock_logger.info.assert_any_call(
            "Cleaning raw files directory: /home/testuser/UCAutomation/downloads/raw_files"
        )
        mock_logger.info.assert_any_call(
            "Cleaning DNG files directory: /home/testuser/UCAutomation/downloads/dng_files"
        )
        mock_logger.info.assert_any_call(
            "Cleanup complete: 1 raw files and 1 DNG files removed"
        )

    @patch("utils.os.path.expanduser")
    @patch("utils.os.path.exists")
    @patch("utils.open", new_callable=mock_open)
    @patch("utils.logger")
    def test_skip_cleanup_if_recent(
        self, mock_logger, mock_open, mock_exists, mock_expanduser
    ):
        """Test cleanup is skipped if last cleanup was recent"""
        # Setup mocks
        mock_expanduser.return_value = "/home/testuser"
        mock_exists.return_value = True

        # Mock reading the last cleanup time (3 days ago)
        current_time = time.time()
        three_days_ago = current_time - (3 * 24 * 60 * 60)
        mock_open().read.return_value = str(three_days_ago)

        # Call function with default 7-day threshold
        result = utils.clean_download_directories()

        # Verify cleanup was skipped
        assert result == (0, 0)
        mock_logger.info.assert_any_call("Last cleanup was 3 days ago. Skipping.")

    @patch("utils.os.path.expanduser")
    @patch("utils.os.path.exists")
    @patch("utils.os.path.isfile")
    @patch("utils.os.path.getmtime")
    @patch("utils.os.remove")
    @patch("utils.os.listdir")
    @patch("utils.time.time")
    @patch("utils.open", new_callable=mock_open)
    @patch("utils.logger")
    def test_files_at_exact_cutoff_threshold(
        self,
        mock_logger,
        mock_open,
        mock_time,
        mock_listdir,
        mock_remove,
        mock_getmtime,
        mock_isfile,
        mock_exists,
        mock_expanduser,
    ):
        """Test that files exactly at the cutoff threshold are handled correctly"""
        # Setup mocks
        mock_expanduser.return_value = "/home/testuser"

        def exists_side_effect(path):
            if path == "/home/testuser/UCAutomation/.last_cleanup":
                return False
            return True

        mock_exists.side_effect = exists_side_effect

        mock_isfile.return_value = True

        days_threshold = 7
        current_time = 100 * 24 * 60 * 60  # 100 days since epoch
        cutoff_time = current_time - (days_threshold * 24 * 60 * 60)
        mock_time.return_value = current_time

        def listdir_side_effect(path):
            if path == "/home/testuser/UCAutomation/downloads/raw_files":
                return [
                    "exact_cutoff.cr3",
                    "just_before_cutoff.cr3",
                    "just_after_cutoff.cr3",
                ]
            elif path == "/home/testuser/UCAutomation/downloads/dng_files":
                return ["exact_cutoff.dng", "newer_file.dng"]
            return []

        mock_listdir.side_effect = listdir_side_effect

        # Set file modification times
        def get_mtime(path):
            if "exact_cutoff" in path:
                return cutoff_time  # Exactly at cutoff threshold
            elif "just_before_cutoff" in path:
                return cutoff_time - 1  # 1 second before cutoff (should be deleted)
            elif "just_after_cutoff" in path:
                return cutoff_time + 1  # 1 second after cutoff (should be kept)
            else:
                return current_time  # New file

        mock_getmtime.side_effect = get_mtime

        result = utils.clean_download_directories(
            base_dir="/home/testuser/UCAutomation", days_threshold=days_threshold
        )

        assert result == (1, 0)

        mock_remove.assert_called_once_with(
            "/home/testuser/UCAutomation/downloads/raw_files/just_before_cutoff.cr3"
        )

        assert not any(
            call[0][0].endswith("exact_cutoff.cr3")
            for call in mock_remove.call_args_list
        )
        assert not any(
            call[0][0].endswith("exact_cutoff.dng")
            for call in mock_remove.call_args_list
        )

        mock_logger.info.assert_any_call(
            "Cleaning raw files directory: /home/testuser/UCAutomation/downloads/raw_files"
        )
        mock_logger.info.assert_any_call(
            "Cleaning DNG files directory: /home/testuser/UCAutomation/downloads/dng_files"
        )
        mock_logger.info.assert_any_call(
            "Cleanup complete: 1 raw files and 0 DNG files removed"
        )

    @patch("utils.os.path.expanduser")
    @patch("utils.os.path.exists")
    @patch("utils.os.listdir")
    @patch("utils.time.time")
    @patch("utils.open", new_callable=mock_open)
    @patch("utils.logger")
    def test_directories_dont_exist(
        self,
        mock_logger,
        mock_open,
        mock_time,
        mock_listdir,
        mock_exists,
        mock_expanduser,
    ):
        """Test when download directories don't exist at all"""
        # Setup mocks
        mock_expanduser.return_value = "/home/testuser"

        # Set current time
        current_time = 100 * 24 * 60 * 60  # 100 days since epoch
        mock_time.return_value = current_time

        # Make directories not exist
        def exists_side_effect(path):
            if path == "/home/testuser/UCAutomation/.last_cleanup":
                return False
            if (
                path == "/home/testuser/UCAutomation/downloads/raw_files"
                or path == "/home/testuser/UCAutomation/downloads/dng_files"
            ):
                return False
            return True

        mock_exists.side_effect = exists_side_effect

        # Call function
        result = utils.clean_download_directories(
            base_dir="/home/testuser/UCAutomation"
        )

        # Verify results
        assert result == (0, 0)  # No files removed as directories don't exist

        # Verify os.listdir was never called
        mock_listdir.assert_not_called()

        # Verify the marker file was still written with the current time
        mock_open.assert_called_with("/home/testuser/UCAutomation/.last_cleanup", "w")
        mock_open().write.assert_called_with(str(current_time))

        # Verify logging - should not see messages about cleaning specific dirs
        # but should see a message about no files needing cleanup
        mock_logger.info.assert_called_with("No files needed cleanup")

        # Check that we didn't try to clean non-existent directories
        for call in mock_logger.info.call_args_list:
            assert "Cleaning raw files directory" not in call[0][0]
            assert "Cleaning DNG files directory" not in call[0][0]


class TestMoveToArchive:
    """Tests for move_to_archive function"""

    def test_move_to_archive_success(self, mock_drive_service):
        """Test successful file moving to archive"""
        # Setup mocks
        mock_drive_service.get_file_status.return_value = {"status": "uploaded"}
        mock_drive_service.move_file.return_value = ["archive_folder_id"]
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.move_to_archive(
            mock_drive_service, test_file, "archive_folder_id"
        )

        # Verify
        assert result is True
        mock_drive_service.get_file_status.assert_called_once_with("file123")
        mock_drive_service.move_file.assert_called_once_with(
            "file123", "archive_folder_id"
        )

    def test_move_to_archive_not_uploaded(self, mock_drive_service):
        """Test handling file with status other than 'uploaded'"""
        # Setup mocks
        mock_drive_service.get_file_status.return_value = {"status": "processed"}
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.move_to_archive(
            mock_drive_service, test_file, "archive_folder_id"
        )

        # Verify
        assert result is False
        mock_drive_service.get_file_status.assert_called_once_with("file123")
        mock_drive_service.move_file.assert_not_called()

    def test_move_to_archive_exception(self, mock_drive_service):
        """Test handling exceptions during file move"""
        # Setup mocks
        mock_drive_service.get_file_status.return_value = {"status": "uploaded"}
        mock_drive_service.move_file.side_effect = Exception("Test error")
        test_file = {"id": "file123", "name": "test.cr3"}

        # Call function
        result = utils.move_to_archive(
            mock_drive_service, test_file, "archive_folder_id"
        )

        # Verify
        assert result is False
        mock_drive_service.get_file_status.assert_called_once_with("file123")
        mock_drive_service.move_file.assert_called_once_with(
            "file123", "archive_folder_id"
        )
