import os
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
    def convert(self, file_path):
        # Placeholder for conversion logic
        print(f"Converting {file_path} to DNG...")
