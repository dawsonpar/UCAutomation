from unittest.mock import Mock

import pytest
from raw_converter import RawFileConverter, RawFileHandler


@pytest.fixture
def raw_file_handler():
    # Create a mock converter
    mock_converter = Mock(spec=RawFileConverter)
    # Create an instance of RawFileHandler with the mock converter
    handler = RawFileHandler(mock_converter)
    return handler, mock_converter


def test_raw_file_handler_on_created(raw_file_handler):
    handler, mock_converter = raw_file_handler

    # Create mock events for different raw file types
    raw_files = [
        "/path/to/file.cr3",
        "/path/to/file.arw",
        "/path/to/file.ARW",
        "/path/to/file.nef",
        "/path/to/file.NEF",
    ]

    for raw_file in raw_files:
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = raw_file

        # Call the on_created method with the mock event
        handler.on_created(mock_event)

        # Assert that the convert method was called with the correct file path
        mock_converter.convert.assert_called_with(raw_file)


def test_raw_file_handler_on_created_non_raw_file(raw_file_handler):
    handler, mock_converter = raw_file_handler

    # Create a mock event for a non-raw file
    mock_event = Mock()
    mock_event.is_directory = False
    mock_event.src_path = "/path/to/file.txt"

    # Call the on_created method with the mock event
    handler.on_created(mock_event)

    # Assert that the convert method was not called
    mock_converter.convert.assert_not_called()


def test_raw_file_handler_on_created_directory(raw_file_handler):
    handler, mock_converter = raw_file_handler

    # Create a mock event for a directory
    mock_event = Mock()
    mock_event.is_directory = True
    mock_event.src_path = "/path/to/directory"

    # Call the on_created method with the mock event
    handler.on_created(mock_event)

    # Assert that the convert method was not called
    mock_converter.convert.assert_not_called()
