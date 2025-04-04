import os
from unittest.mock import MagicMock, patch

import pytest

from firestore_service import FirestoreService


@pytest.fixture
def mock_firestore():
    """Setup mock Firestore client"""
    with patch(
        "firestore_service.service_account.Credentials.from_service_account_file"
    ) as mock_creds, patch("firestore_service.firestore.Client") as mock_client_cls:

        # Setup mock document handling
        mock_doc = MagicMock()
        mock_collection = MagicMock()
        mock_collection.document.return_value = mock_doc

        mock_db = MagicMock()
        mock_db.collection.return_value = mock_collection

        mock_client_cls.return_value = mock_db

        yield {
            "creds": mock_creds,
            "client_cls": mock_client_cls,
            "db": mock_db,
            "collection": mock_collection,
            "doc": mock_doc,
        }


def test_init_with_env_var(mock_firestore):
    """Test initializing FirestoreService with environment variable"""
    with patch.dict(
        os.environ, {"FIREBASE_CREDENTIALS_PATH": "/path/to/creds.json"}
    ), patch("os.path.exists", return_value=True):

        service = FirestoreService()

        mock_firestore["creds"].assert_called_once_with("/path/to/creds.json")
        mock_firestore["client_cls"].assert_called_once()
        assert service.collection == mock_firestore["collection"]


def test_init_with_param(mock_firestore):
    """Test initializing FirestoreService with explicit param"""
    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/custom/path.json")

        mock_firestore["creds"].assert_called_once_with("/custom/path.json")
        mock_firestore["client_cls"].assert_called_once()


def test_init_missing_credentials():
    """Test error when credentials are missing"""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(
            ValueError, match="FIREBASE_CREDENTIALS_PATH environment variable not set"
        ):
            FirestoreService()


def test_init_nonexistent_file():
    """Test error when credentials file doesn't exist"""
    with patch.dict(
        os.environ, {"FIREBASE_CREDENTIALS_PATH": "/nonexistent/path.json"}
    ), patch("os.path.exists", return_value=False):

        with pytest.raises(
            FileNotFoundError, match="Firebase credentials file not found"
        ):
            FirestoreService()


def test_mark_as_processing_new_file(mock_firestore):
    """Test marking a new file as processing"""
    # Setup document snapshot behavior
    mock_snapshot = MagicMock()
    mock_snapshot.exists = False
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.uname") as mock_uname, patch("os.path.exists", return_value=True):
        mock_uname.return_value.nodename = "test-machine"

        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.mark_as_processing("file123")

        assert result is True
        mock_firestore["doc"].set.assert_called_once()
        args = mock_firestore["doc"].set.call_args[0][0]
        assert args["status"] == "processing"
        assert args["machine_id"] == "test-machine"
        assert "updated_at" in args


def test_mark_as_processing_already_processing(mock_firestore):
    """Test marking a file that's already being processed"""
    # Setup document snapshot behavior for already processing file
    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {
        "status": "processing",
        "machine_id": "other-machine",
        "updated_at": "2023-01-01T12:00:00",
    }
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.mark_as_processing("file123")

        assert result is False  # Should return False as already processing
        mock_firestore["doc"].set.assert_not_called()


def test_mark_as_processed(mock_firestore):
    """Test marking a file as processed"""
    with patch("os.uname") as mock_uname, patch("os.path.exists", return_value=True):
        mock_uname.return_value.nodename = "test-machine"

        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.mark_as_processed(
            "file123", additional_data={"filename": "test.mp4"}
        )

        assert result is True
        mock_firestore["doc"].set.assert_called_once()
        args = mock_firestore["doc"].set.call_args[0][0]
        assert args["status"] == "processed"
        assert args["machine_id"] == "test-machine"
        assert args["filename"] == "test.mp4"
        assert "updated_at" in args
        assert "processed_at" in args


def test_is_processed_true(mock_firestore):
    """Test checking if a file is processed (when it is)"""
    # Setup document snapshot behavior
    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {"status": "processed"}
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.is_processed("file123")

        assert result is True


def test_is_processed_false_status(mock_firestore):
    """Test checking if a file is processed (when status is not processed)"""
    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = {"status": "processing"}
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.is_processed("file123")

        assert result is False


def test_is_processed_not_found(mock_firestore):
    """Test checking if a file is processed (when not found)"""
    mock_snapshot = MagicMock()
    mock_snapshot.exists = False
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.is_processed("file123")

        assert result is False


def test_get_file_status(mock_firestore):
    """Test getting file status"""
    file_data = {
        "status": "processed",
        "machine_id": "test-machine",
        "updated_at": "2023-01-01T12:00:00",
    }

    mock_snapshot = MagicMock()
    mock_snapshot.exists = True
    mock_snapshot.to_dict.return_value = file_data
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.get_file_status("file123")

        assert result == file_data


def test_get_file_status_not_found(mock_firestore):
    """Test getting file status when not found"""
    mock_snapshot = MagicMock()
    mock_snapshot.exists = False
    mock_firestore["doc"].get.return_value = mock_snapshot

    with patch("os.path.exists", return_value=True):
        service = FirestoreService(credentials_path="/fake/path.json")
        result = service.get_file_status("file123")

        assert result is None
