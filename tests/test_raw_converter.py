import json
import os
from unittest.mock import MagicMock, Mock, patch

import pytest

from raw_converter import RawFileConverter


@pytest.fixture
def raw_file_converter(tmp_path):
    """Fixture to create a RawFileConverter instance with a temporary processed files path."""
    processed_files_path = tmp_path / "processed_files.json"
    return RawFileConverter(str(processed_files_path))


@patch("subprocess.run")
def test_raw_file_converter_success(mock_subprocess, raw_file_converter):
    """Test RawFileConverter successfully converts a file."""
    mock_subprocess.return_value = MagicMock(returncode=0)

    input_file = "/path/to/file.cr3"
    output_dir = "/path/to/output"

    result = raw_file_converter.convert(input_file, output_dir)

    assert result is True
    mock_subprocess.assert_called_once_with(
        [
            "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter",
            "-c",
            "-s",
            "-d",
            output_dir,
            input_file,
        ],
        capture_output=True,
        text=True,
    )


@patch("subprocess.run")
def test_raw_file_converter_failure(mock_subprocess, raw_file_converter):
    """Test RawFileConverter handles failed conversion."""
    mock_subprocess.return_value = MagicMock(returncode=1, stderr="Conversion error")

    input_file = "/path/to/file.cr3"
    output_dir = "/path/to/output"

    with pytest.raises(Exception):
        raw_file_converter.convert(input_file, output_dir)

    mock_subprocess.assert_called_once()


def test_raw_file_converter_tracks_processed_files(raw_file_converter):
    """Test RawFileConverter tracks processed files in JSON."""
    input_file = "file.cr3"

    raw_file_converter.mark_as_processed(input_file)

    assert raw_file_converter.is_processed(input_file) is True


def test_raw_file_converter_does_not_reprocess(raw_file_converter):
    """Test RawFileConverter skips already processed files."""
    input_file = "file.cr3"
    output_dir = "/path/to/output"

    raw_file_converter.mark_as_processed(input_file)

    with patch("subprocess.run") as mock_subprocess:
        result = raw_file_converter.convert(input_file, output_dir)
        assert result is False
        mock_subprocess.assert_not_called()


def test_raw_file_converter_persistence(raw_file_converter):
    """Test RawFileConverter persists processed files to JSON."""
    input_file = "file.cr3"
    raw_file_converter.mark_as_processed(input_file)

    with open(raw_file_converter.processed_files_path, "r") as f:
        data = json.load(f)

    assert input_file in data["processed"]


def test_raw_file_converter_creates_processed_files_json(tmp_path):
    """Test RawFileConverter creates processed_files.json if it doesn't exist."""
    processed_files_path = tmp_path / "processed_files.json"
    assert not os.path.exists(processed_files_path)

    raw_file_converter = RawFileConverter(str(processed_files_path))

    assert os.path.exists(processed_files_path)
    with open(processed_files_path, "r") as f:
        data = json.load(f)
    assert data == {"processed": []}
