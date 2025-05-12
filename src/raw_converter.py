import os
import subprocess
import threading

from firestore_service import FirestoreService
from log_config import get_logger

logger = get_logger()


class RawFileConverter:
    def __init__(
        self,
        firestore_service=None,
        firebase_credentials_path=None,
        collection_name="processed_files",
    ):
        """Initialize the RawFileConverter

        Args:
            firestore_service: An existing FirestoreService instance or None to create a new one
            firebase_credentials_path: Path to Firebase credentials file (if creating a new service)
            collection_name: Name of the Firestore collection to use
        """
        if firestore_service:
            self.firestore_service = firestore_service
        else:
            self.firestore_service = FirestoreService(
                collection_name=collection_name,
                credentials_path=firebase_credentials_path,
            )
        self.lock = threading.Lock()

    def is_processed(self, file_id):
        """Check if the file has already been processed using Firestore."""
        return self.firestore_service.is_processed(file_id)

    def is_uploaded(self, file_id):
        """Check if the file has already been uploaded using Firestore."""
        return self.firestore_service.is_uploaded(file_id)

    def mark_as_processing(self, file_id, machine_id=None):
        """Mark a file as currently being processed in Firestore.

        Returns:
            bool: True if successfully marked as processing, False if already being processed
        """
        with self.lock:
            return self.firestore_service.mark_as_processing(file_id, machine_id)

    def mark_as_processed(self, file_id, machine_id=None, additional_data=None):
        """Mark a file as processed and update Firestore."""
        with self.lock:
            return self.firestore_service.mark_as_processed(
                file_id, machine_id, additional_data
            )

    def mark_as_failed(self, file_id, error_message=None, machine_id=None):
        """Mark a file as failed and update Firestore."""
        with self.lock:
            return self.firestore_service.mark_as_failed(
                file_id, error_message, machine_id
            )

    def convert(self, file_path, output_dir, file_id=None, already_marked=False):
        """Convert a raw file to DNG format

        Args:
            file_path: Path to the raw file
            output_dir: Directory to output the converted DNG file
            file_id: Google Drive file ID (used for tracking in Firestore)
            already_marked: If True, skip the mark_as_processing check

        Returns:
            bool: True if conversion was successful, False if skipped

        Raises:
            RuntimeError: If conversion fails
        """
        file_name = os.path.basename(file_path)

        # Use file_name as file_id if not provided
        if file_id is None:
            file_id = file_name

        if self.is_uploaded(file_id):
            logger.info(f"Skipping {file_name}, already uploaded.")
            return False

        if self.is_processed(file_id):
            logger.info(f"Skipping {file_name}, already processed.")
            return False

        # Try to mark file as processing, return if already being processed
        if not already_marked and not self.mark_as_processing(file_id):
            logger.info(
                f"Skipping {file_name}, already being processed by another machine."
            )
            return False

        converter_path = (
            "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter"
        )

        # Check if converter exists
        if not os.path.exists(converter_path):
            error_message = f"Adobe DNG Converter not found at {converter_path}"
            logger.error(error_message)
            self.mark_as_failed(file_id, error_message)
            raise FileNotFoundError(error_message)

        command = [converter_path, "-c", "-s", "-d", output_dir, file_path]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                dng_file_name = os.path.splitext(file_name)[0] + ".dng"
                dng_file_path = os.path.join(output_dir, dng_file_name)

                # Verify the file was actually created
                if not os.path.exists(dng_file_path):
                    error_message = (
                        f"DNG file not found after conversion: {dng_file_path}"
                    )
                    logger.error(error_message)
                    self.mark_as_failed(file_id, error_message)
                    return False

                logger.info(f"Successfully converted {file_path} to DNG.")

                # Mark as processed with relevant metadata
                additional_data = {
                    "original_filename": file_name,
                    "converted_filename": dng_file_name,
                    "dng_file_path": dng_file_path,
                }
                self.mark_as_processed(file_id, None, additional_data)

                return True
            else:
                error_message = f"Error converting {file_path}: {result.stderr}"
                logger.error(error_message)
                self.mark_as_failed(file_id, error_message)
                raise RuntimeError(error_message)
        except Exception as e:
            error_message = f"Exception while converting {file_path}: {str(e)}"
            logger.error(error_message)

            # Only mark as failed if it's not already a RuntimeError from above
            if not isinstance(e, RuntimeError) or "Error converting" not in str(e):
                self.mark_as_failed(file_id, error_message)

            raise
