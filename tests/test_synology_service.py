import unittest
from unittest.mock import MagicMock, patch

from synology_service import SynologyService


class TestSynologyService(unittest.TestCase):
    @patch("synology_service.FileStation")
    def test_upload_success(self, mock_filestation):
        # Arrange
        mock_instance = mock_filestation.return_value
        mock_instance.upload_file.return_value = {
            "data": {"file": "file.txt"},
            "success": True,
        }
        service = SynologyService()

        # Act
        result = service.upload(
            "1.2.3.4", 5001, "user", "pass", "/tmp/file.txt", "/folder"
        )

        # Assert
        self.assertTrue(result)
        mock_instance.upload_file.assert_called_once_with(
            "/folder", "/tmp/file.txt", overwrite=False
        )

    @patch("synology_service.FileStation")
    def test_upload_failure(self, mock_filestation):
        # Arrange
        mock_instance = mock_filestation.return_value
        # Simulate error tuple as returned by FileStation
        mock_instance.upload_file.return_value = (
            None,
            {"success": False, "error": 123},
        )
        service = SynologyService()

        # Act
        result = service.upload(
            "1.2.3.4", 5001, "user", "pass", "/tmp/file.txt", "/folder"
        )

        # Assert
        self.assertFalse(result)
        mock_instance.upload_file.assert_called_once_with(
            "/folder", "/tmp/file.txt", overwrite=False
        )

    @patch("synology_service.FileStation")
    def test_upload_exception(self, mock_filestation):
        # Arrange
        mock_instance = mock_filestation.return_value
        mock_instance.upload_file.side_effect = Exception("Upload failed!")
        service = SynologyService()

        # Act
        result = service.upload(
            "1.2.3.4", 5001, "user", "pass", "/tmp/file.txt", "/folder"
        )

        # Assert
        self.assertFalse(result)
        mock_instance.upload_file.assert_called_once_with(
            "/folder", "/tmp/file.txt", overwrite=False
        )

    @patch("synology_service.FileStation")
    def test_upload_invalid_folder_path(self, mock_filestation):
        # Arrange
        mock_instance = mock_filestation.return_value
        # Simulate invalid folder_path response
        mock_instance.upload_file.return_value = (
            200,
            {"error": {"code": 407}, "success": False},
        )
        service = SynologyService()

        # Act
        result = service.upload(
            "1.2.3.4", 5001, "user", "pass", "/tmp/file.txt", "/invalid_folder"
        )

        # Assert
        self.assertFalse(result)
        mock_instance.upload_file.assert_called_once_with(
            "/invalid_folder", "/tmp/file.txt", overwrite=False
        )


if __name__ == "__main__":
    unittest.main()
