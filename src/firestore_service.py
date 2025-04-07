import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from google.cloud import firestore
from google.oauth2 import service_account

load_dotenv()

# Configure logging
log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class FirestoreService:
    """Service for tracking file processing status in Firestore."""

    def __init__(self, collection_name="processed_files", credentials_path=None):
        """Initialize Firestore service.

        Args:
            collection_name: Name of the Firestore collection to use
            credentials_path: Path to Firebase credentials JSON file
        """
        credentials_path = credentials_path or os.environ.get(
            "FIREBASE_CREDENTIALS_PATH"
        )
        if not credentials_path:
            raise ValueError("FIREBASE_CREDENTIALS_PATH environment variable not set.")

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials file not found at {credentials_path}"
            )

        # Create credentials and client
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        self.db = firestore.Client(credentials=credentials)
        self.collection = self.db.collection(collection_name)

    def mark_as_processing(self, file_id, machine_id=None):
        """Mark a file as currently being processed.

        Args:
            file_id: Google Drive file ID
            machine_id: Identifier for the machine doing the processing

        Returns:
            bool: True if successfully marked as processing, False if already being processed
        """
        doc_ref = self.collection.document(file_id)
        doc = doc_ref.get()

        # Get machine ID (hostname if not provided)
        if not machine_id:
            machine_id = os.uname().nodename

        current_time = datetime.now().isoformat()

        if doc.exists:
            data = doc.to_dict()
            if data.get("status") == "processing":
                processing_time = data.get("updated_at")
                machine = data.get("machine_id")
                logging.info(
                    f"File {file_id} is already being processed by {machine} since {processing_time}"
                )
                return False

        # Set or update the document
        doc_ref.set(
            {
                "status": "processing",
                "machine_id": machine_id,
                "updated_at": current_time,
                "retry_count": 0,
            }
        )

        logging.info(f"Marked file {file_id} as processing by {machine_id}")
        return True

    def mark_as_processed(self, file_id, machine_id=None, additional_data=None):
        """Mark a file as successfully processed.

        Args:
            file_id: Google Drive file ID
            machine_id: Identifier for the machine that did the processing
            additional_data: Optional dictionary with additional information to store

        Returns:
            bool: True if successfully marked as processed
        """
        doc_ref = self.collection.document(file_id)

        # Get machine ID (hostname if not provided)
        if not machine_id:
            machine_id = os.uname().nodename

        current_time = datetime.now().isoformat()

        data = {
            "status": "processed",
            "machine_id": machine_id,
            "updated_at": current_time,
            "processed_at": current_time,
        }

        # Add any additional data
        if additional_data and isinstance(additional_data, dict):
            data.update(additional_data)

        doc_ref.set(data)

        logging.info(f"Marked file {file_id} as processed by {machine_id}")
        return True

    def is_processed(self, file_id):
        """Check if a file has already been processed.

        Args:
            file_id: Google Drive file ID

        Returns:
            bool: True if the file has been processed
        """
        doc_ref = self.collection.document(file_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        data = doc.to_dict()
        return data.get("status") == "processed"

    def get_file_status(self, file_id):
        """Get the current status of a file.

        Args:
            file_id: Google Drive file ID

        Returns:
            dict: File status information or None if not found
        """
        doc_ref = self.collection.document(file_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return doc.to_dict()

    def mark_as_failed(self, file_id, machine_id=None, error_message=None):
        """Mark a file as failed processing.

        Args:
            file_id: Google Drive file ID
            machine_id: Identifier for the machine that failed processing
            error_message: Optional error message describing the failure

        Returns:
            bool: True if successfully marked as failed
        """
        doc_ref = self.collection.document(file_id)

        # Get machine ID (hostname if not provided)
        if not machine_id:
            machine_id = os.uname().nodename

        current_time = datetime.now().isoformat()

        # Get current retry count
        doc = doc_ref.get()
        retry_count = 0
        if doc.exists:
            data = doc.to_dict()
            retry_count = data.get("retry_count", 0)

        data = {
            "status": "failed",
            "machine_id": machine_id,
            "updated_at": current_time,
            "failed_at": current_time,
            "retry_count": retry_count + 1,
        }

        if error_message:
            data["error_message"] = error_message

        doc_ref.set(data)

        logging.error(f"Marked file {file_id} as failed by {machine_id}")
        return True
