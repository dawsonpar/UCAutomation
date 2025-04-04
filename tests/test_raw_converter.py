import os
from unittest.mock import MagicMock, patch

import pytest

from raw_converter import RawFileConverter


@pytest.fixture
def mock_firestore_service():
    mock_service = MagicMock()
    mock_service.is_processed.return_value = False
    mock_service.mark_as_processing.return_value = True
    mock_service.mark_as_processed.return_value = True
    return mock_service


def test_init_with_service(mock_firestore_service):
    """Test initializing with an existing FirestoreService."""
    converter = RawFileConverter(firestore_service=mock_firestore_service)
    assert converter.firestore_service == mock_firestore_service


def test_init_creates_service():
    """Test initializing without a service creates a new FirestoreService."""
    with patch("raw_converter.FirestoreService") as mock_firestore_cls:
        mock_service = MagicMock()
        mock_firestore_cls.return_value = mock_service

        converter = RawFileConverter(firebase_credentials_path="/fake/path.json")

        mock_firestore_cls.assert_called_once_with(
            collection_name="processed_files", credentials_path="/fake/path.json"
        )
        assert converter.firestore_service == mock_service


def test_is_processed(mock_firestore_service):
    """Test checking if a file is processed."""
    file_id = "test_file_id"

    # Setup the mock to return True
    mock_firestore_service.is_processed.return_value = True

    converter = RawFileConverter(firestore_service=mock_firestore_service)
    result = converter.is_processed(file_id)

    assert result is True
    mock_firestore_service.is_processed.assert_called_once_with(file_id)


def test_mark_as_processing(mock_firestore_service):
    """Test marking a file as processing."""
    file_id = "test_file_id"
    machine_id = "test-machine"

    converter = RawFileConverter(firestore_service=mock_firestore_service)
    result = converter.mark_as_processing(file_id, machine_id)

    assert result is True
    mock_firestore_service.mark_as_processing.assert_called_once_with(
        file_id, machine_id
    )


def test_mark_as_processed(mock_firestore_service):
    """Test marking a file as processed."""
    file_id = "test_file_id"
    machine_id = "test-machine"
    additional_data = {"filename": "test.dng"}

    converter = RawFileConverter(firestore_service=mock_firestore_service)
    result = converter.mark_as_processed(file_id, additional_data, machine_id)

    assert result is True
    mock_firestore_service.mark_as_processed.assert_called_once_with(
        file_id, machine_id, additional_data
    )


def test_convert_already_processed(mock_firestore_service):
    """Test convert when file is already processed."""
    file_path = "/tmp/test.cr3"
    output_dir = "/tmp/output"
    file_id = "test_file_id"

    # Setup to return already processed
    mock_firestore_service.is_processed.return_value = True

    converter = RawFileConverter(firestore_service=mock_firestore_service)
    result = converter.convert(file_path, output_dir, file_id)

    assert result is False
    mock_firestore_service.is_processed.assert_called_once_with(file_id)
    mock_firestore_service.mark_as_processing.assert_not_called()


def test_convert_already_processing(mock_firestore_service):
    """Test convert when file is already being processed by another machine."""
    file_path = "/tmp/test.cr3"
    output_dir = "/tmp/output"
    file_id = "test_file_id"

    # Setup to return not processed but already processing
    mock_firestore_service.is_processed.return_value = False
    mock_firestore_service.mark_as_processing.return_value = False

    converter = RawFileConverter(firestore_service=mock_firestore_service)
    result = converter.convert(file_path, output_dir, file_id)

    assert result is False
    mock_firestore_service.is_processed.assert_called_once_with(file_id)
    mock_firestore_service.mark_as_processing.assert_called_once()


def test_convert_missing_converter():
    """Test convert when Adobe DNG Converter is missing."""
    file_path = "/tmp/test.cr3"
    output_dir = "/tmp/output"
    file_id = "test_file_id"

    with patch("raw_converter.FirestoreService") as mock_firestore_cls:
        mock_service = MagicMock()
        mock_service.is_processed.return_value = False
        mock_service.mark_as_processing.return_value = True
        mock_firestore_cls.return_value = mock_service

        with patch("os.path.exists", return_value=False):
            converter = RawFileConverter()

            with pytest.raises(
                FileNotFoundError, match="Adobe DNG Converter not found"
            ):
                converter.convert(file_path, output_dir, file_id)


def test_convert_successful():
    """Test successful conversion."""
    file_path = "/tmp/test.cr3"
    output_dir = "/tmp/output"
    file_id = "test_file_id"

    with patch("raw_converter.FirestoreService") as mock_firestore_cls:
        mock_service = MagicMock()
        mock_service.is_processed.return_value = False
        mock_service.mark_as_processing.return_value = True
        mock_firestore_cls.return_value = mock_service

        # Mock converter existence and subprocess
        with patch("os.path.exists", return_value=True), patch(
            "subprocess.run"
        ) as mock_run:

            # Make subprocess.run return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            mock_run.return_value = mock_process

            converter = RawFileConverter()
            result = converter.convert(file_path, output_dir, file_id)

            assert result is True
            mock_service.mark_as_processed.assert_called_once()

            args = mock_service.mark_as_processed.call_args[0]
            assert args[0] == file_id  # file_id
            assert args[2] is not None  # additional_data is the third parameter
            assert isinstance(args[2], dict)
            assert args[2]["original_filename"] == os.path.basename(file_path)
            assert args[2]["converted_filename"] == "test.dng"


def test_convert_failure():
    """Test failed conversion."""
    file_path = "/tmp/test.cr3"
    output_dir = "/tmp/output"
    file_id = "test_file_id"

    with patch("raw_converter.FirestoreService") as mock_firestore_cls:
        mock_service = MagicMock()
        mock_service.is_processed.return_value = False
        mock_service.mark_as_processing.return_value = True
        mock_firestore_cls.return_value = mock_service

        # Mock converter existence and subprocess
        with patch("os.path.exists", return_value=True), patch(
            "subprocess.run"
        ) as mock_run:

            # Make subprocess.run return failure
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "Conversion error"
            mock_run.return_value = mock_process

            converter = RawFileConverter()

            with pytest.raises(RuntimeError, match="Error converting"):
                converter.convert(file_path, output_dir, file_id)

            # Should not mark as processed on failure
            mock_service.mark_as_processed.assert_not_called()
