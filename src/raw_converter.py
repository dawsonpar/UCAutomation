import json
import logging
import os
import subprocess
import threading
import time

# Configure logging
log_file = os.path.expanduser("~/UCAutomation/lib/rawconverter_out.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class RawFileConverter:
    def __init__(self, processed_files_path):
        self.processed_files_path = processed_files_path
        self.lock = threading.Lock()
        self._load_processed_files()

    def _load_processed_files(self):
        """Load the processed files from JSON."""
        if not os.path.exists(self.processed_files_path):
            self.processed_files = {"processed": []}
            self._save_processed_files()
        else:
            with open(self.processed_files_path, "r") as f:
                self.processed_files = json.load(f)

    def _save_processed_files(self):
        """Save the processed files to JSON."""
        os.makedirs(os.path.dirname(self.processed_files_path), exist_ok=True)
        with self.lock:
            with open(self.processed_files_path, "w") as f:
                json.dump(self.processed_files, f, indent=4)

    def is_processed(self, file_name):
        """Check if the file has already been processed."""
        return file_name in self.processed_files["processed"]

    def mark_as_processed(self, file_name):
        """Mark a file as processed and update the JSON file."""
        if file_name not in self.processed_files["processed"]:
            self.processed_files["processed"].append(file_name)
            self._save_processed_files()

    def convert(self, file_path, output_dir):
        file_name = os.path.basename(file_path)

        if self.is_processed(file_name):
            logging.info(f"Skipping {file_name}, already processed.")
            return False

        converter_path = (
            "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter"
        )

        command = [converter_path, "-c", "-s", "-d", output_dir, file_path]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"Successfully converted {file_path} to DNG.")
            self.mark_as_processed(file_name)
            return True
        else:
            error_message = f"Error converting {file_path}: {result.stderr}"
            logging.error(error_message)
            raise RuntimeError(error_message)
