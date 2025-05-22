import sys
import unittest
from unittest.mock import MagicMock, patch

# Patch sys.modules so we can import main.py even if dependencies are missing
sys.modules["google_drive_service"] = MagicMock()
sys.modules["log_config"] = MagicMock()
sys.modules["raw_converter"] = MagicMock()
sys.modules["synology_service"] = MagicMock()
sys.modules["utils"] = MagicMock()

import main as main_mod


class TestStatusCases(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(
            "os.environ",
            {
                "INGEST_FOLDER_ID": "folder_id",
                "DNG_FOLDER_ID": "dng_folder_id",
                "NAS_DEST_PATH": "nas_dest_path",
                "ARCHIVE_FOLDER_ID": "archive_folder_id",
                "GOOGLE_CREDENTIALS_PATH": "google_creds_path",
                "FIREBASE_CREDENTIALS_PATH": "firebase_creds_path",
                "NAS_IP": "nas_ip",
                "NAS_PORT": "nas_port",
                "NAS_USER": "nas_user",
                "NAS_PWD": "nas_pwd",
            },
        )
        self.env_patch.start()
        self.uname_patch = patch(
            "os.uname", return_value=type("Uname", (), {"nodename": "test_machine"})()
        )
        self.uname_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.uname_patch.stop()

    def run_main_with_status(self, status_value):
        # Patch all external dependencies
        with patch("main.load_dotenv"), patch("main.get_logger"), patch(
            "main.clean_download_directories", return_value=(0, 0)
        ), patch("main.get_quota", return_value={"usage_percentage": 10}), patch(
            "main.SynologyService"
        ) as mock_synology, patch(
            "main.GoogleDriveService"
        ) as mock_drive_service_cls, patch(
            "main.RawFileConverter"
        ) as mock_converter_cls, patch(
            "main.move_to_archive"
        ) as mock_move_to_archive:

            # Setup mocks
            mock_synology.return_value.get_api_info.return_value = {}
            mock_synology.return_value.upload.return_value = True
            mock_drive_service = MagicMock()
            mock_drive_service.list_files.return_value = [
                {"id": "file1", "name": "test1.cr3"},
                {"id": "file2", "name": "test2.arw"},
            ]
            # get_file_status returns the test value for each file
            mock_drive_service.get_file_status.return_value = status_value
            mock_drive_service_cls.return_value = mock_drive_service
            mock_converter_cls.return_value = MagicMock()

            # Run main
            main_mod.main()
            return mock_drive_service, mock_move_to_archive

    def test_status_uploaded(self):
        mock_drive_service, mock_move_to_archive = self.run_main_with_status(
            {"status": "uploaded"}
        )
        # Should skip processing, so mark_file_as_processing should not be called
        self.assertFalse(mock_drive_service.mark_file_as_processing.called)
        self.assertFalse(mock_move_to_archive.called)

    def test_status_processed(self):
        mock_drive_service, mock_move_to_archive = self.run_main_with_status(
            {"status": "processed"}
        )
        self.assertFalse(mock_drive_service.mark_file_as_processing.called)
        self.assertFalse(mock_move_to_archive.called)

    def test_status_processing(self):
        mock_drive_service, mock_move_to_archive = self.run_main_with_status(
            {"status": "processing"}
        )
        self.assertFalse(mock_drive_service.mark_file_as_processing.called)
        self.assertFalse(mock_move_to_archive.called)

    def test_status_failed(self):
        mock_drive_service, mock_move_to_archive = self.run_main_with_status(
            {"status": "failed"}
        )
        # Should process the file (mark_file_as_processing called)
        self.assertTrue(mock_drive_service.mark_file_as_processing.called)
        self.assertTrue(mock_move_to_archive.called)

    def test_status_none(self):
        mock_drive_service, mock_move_to_archive = self.run_main_with_status(None)
        # Should process the file (mark_file_as_processing called)
        self.assertTrue(mock_drive_service.mark_file_as_processing.called)
        self.assertTrue(mock_move_to_archive.called)


class TestDownloadCases(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(
            "os.environ",
            {
                "INGEST_FOLDER_ID": "folder_id",
                "DNG_FOLDER_ID": "dng_folder_id",
                "NAS_DEST_PATH": "nas_dest_path",
                "ARCHIVE_FOLDER_ID": "archive_folder_id",
                "GOOGLE_CREDENTIALS_PATH": "google_creds_path",
                "FIREBASE_CREDENTIALS_PATH": "firebase_creds_path",
                "NAS_IP": "nas_ip",
                "NAS_PORT": "nas_port",
                "NAS_USER": "nas_user",
                "NAS_PWD": "nas_pwd",
            },
        )
        self.env_patch.start()
        self.uname_patch = patch(
            "os.uname", return_value=type("Uname", (), {"nodename": "test_machine"})()
        )
        self.uname_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.uname_patch.stop()

    def run_main_with_download_result(self, download_success=True):
        with patch("main.load_dotenv"), patch("main.get_logger"), patch(
            "main.clean_download_directories", return_value=(0, 0)
        ), patch("main.get_quota", return_value={"usage_percentage": 10}), patch(
            "main.SynologyService"
        ) as mock_synology, patch(
            "main.GoogleDriveService"
        ) as mock_drive_service_cls, patch(
            "main.RawFileConverter"
        ) as mock_converter_cls, patch(
            "main.move_to_archive"
        ) as mock_move_to_archive:

            mock_synology.return_value.get_api_info.return_value = {}
            mock_synology.return_value.upload.return_value = True
            mock_drive_service = MagicMock()
            mock_drive_service.list_files.return_value = [
                {"id": "file1", "name": "test1.cr3"},
            ]
            # get_file_status returns None so file is processed
            mock_drive_service.get_file_status.return_value = None
            mock_drive_service.download_file.return_value = download_success
            mock_drive_service_cls.return_value = mock_drive_service
            mock_converter_cls.return_value = MagicMock()

            main_mod.main()
            return mock_drive_service

    def test_download_file_failure(self):
        mock_drive_service = self.run_main_with_download_result(download_success=False)
        # Should call mark_file_as_failed if download fails
        self.assertTrue(mock_drive_service.mark_file_as_failed.called)
        self.assertTrue(mock_drive_service.download_file.called)

    def test_download_file_success(self):
        mock_drive_service = self.run_main_with_download_result(download_success=True)
        # Should not call mark_file_as_failed if download succeeds
        self.assertFalse(mock_drive_service.mark_file_as_failed.called)
        self.assertTrue(mock_drive_service.download_file.called)


class TestConversionCases(unittest.TestCase):
    def setUp(self):
        self.env_patch = patch.dict(
            "os.environ",
            {
                "INGEST_FOLDER_ID": "folder_id",
                "DNG_FOLDER_ID": "dng_folder_id",
                "NAS_DEST_PATH": "nas_dest_path",
                "ARCHIVE_FOLDER_ID": "archive_folder_id",
                "GOOGLE_CREDENTIALS_PATH": "google_creds_path",
                "FIREBASE_CREDENTIALS_PATH": "firebase_creds_path",
                "NAS_IP": "nas_ip",
                "NAS_PORT": "nas_port",
                "NAS_USER": "nas_user",
                "NAS_PWD": "nas_pwd",
            },
        )
        self.env_patch.start()
        self.uname_patch = patch(
            "os.uname", return_value=type("Uname", (), {"nodename": "test_machine"})()
        )
        self.uname_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.uname_patch.stop()

    def run_main_with_conversion_result(self, convert_success=True):
        with patch("main.load_dotenv"), patch("main.get_logger"), patch(
            "main.clean_download_directories", return_value=(0, 0)
        ), patch("main.get_quota", return_value={"usage_percentage": 10}), patch(
            "main.SynologyService"
        ) as mock_synology, patch(
            "main.GoogleDriveService"
        ) as mock_drive_service_cls, patch(
            "main.RawFileConverter"
        ) as mock_converter_cls, patch(
            "main.move_to_archive"
        ) as mock_move_to_archive:

            mock_synology.return_value.get_api_info.return_value = {}
            mock_synology.return_value.upload.return_value = True
            mock_drive_service = MagicMock()
            mock_drive_service.list_files.return_value = [
                {"id": "file1", "name": "test1.cr3"},
            ]
            mock_drive_service.get_file_status.return_value = {"status": "failed"}
            mock_drive_service.download_file.return_value = True
            mock_drive_service_cls.return_value = mock_drive_service
            mock_converter = MagicMock()
            mock_converter.convert.return_value = convert_success
            mock_converter_cls.return_value = mock_converter

            main_mod.main()
            return mock_drive_service, mock_converter, mock_move_to_archive

    def test_conversion_success(self):
        mock_drive_service, mock_converter, mock_move_to_archive = (
            self.run_main_with_conversion_result(convert_success=True)
        )
        # Should not call mark_file_as_failed if conversion succeeds
        self.assertFalse(mock_drive_service.mark_file_as_failed.called)
        self.assertTrue(mock_converter.convert.called)
        self.assertTrue(mock_move_to_archive.called)

    def test_conversion_failure(self):
        mock_drive_service, mock_converter, mock_move_to_archive = (
            self.run_main_with_conversion_result(convert_success=False)
        )
        # Should call mark_file_as_failed if conversion fails
        self.assertTrue(mock_drive_service.mark_file_as_failed.called)
        self.assertTrue(mock_converter.convert.called)
        self.assertFalse(mock_move_to_archive.called)


if __name__ == "__main__":
    unittest.main()
