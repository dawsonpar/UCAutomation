import os
import subprocess
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class RawFileHandler(FileSystemEventHandler):
    def __init__(self, converter):
        self.converter = converter

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith((".cr3", ".arw", ".nef", ".ARW", ".NEF")):
            print(f"Detected raw file: {event.src_path}")
            self.converter.convert(event.src_path)


class RawFileConverter:
    def convert(self, file_path, output_dir):
        converter_path = (
            "/Applications/Adobe DNG Converter.app/Contents/MacOS/Adobe DNG Converter"
        )

        command = [converter_path, "-c", "-s", "-d", output_dir, file_path]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Successfully converted {file_path} to DNG.")
        else:
            error_message = f"Error converting {file_path}: {result.stderr}"
            print(error_message)
            raise RuntimeError(error_message)
