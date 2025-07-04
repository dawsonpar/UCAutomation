#!/usr/bin/env python3
"""
Utility functions for the UCAutomation project
"""

import logging
import os
import shutil
import sys
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv

from google_drive_service import GoogleDriveService
from log_config import get_logger

logger = get_logger()


def format_size(size_bytes):
    """Convert bytes to a human-readable format."""
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    return f"{size:.2f} {units[i]}"


def get_quota():
    """Check and display Google Drive quota for a service account"""
    load_dotenv()

    folder_id = os.environ.get("INGEST_FOLDER_ID")
    google_creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")

    missing_vars = []
    if not folder_id:
        missing_vars.append("INGEST_FOLDER_ID")
    if not google_creds_path:
        missing_vars.append("GOOGLE_CREDENTIALS_PATH")
    if not firebase_creds_path:
        missing_vars.append("FIREBASE_CREDENTIALS_PATH")

    if missing_vars:
        print(
            f"Error: Missing required environment variables: {', '.join(missing_vars)}"
        )
        return None

    try:
        drive_service = GoogleDriveService(
            folder_id=folder_id,
            credentials_path=google_creds_path,
            firebase_credentials_path=firebase_creds_path,
        )

        quota_info = drive_service.get_storage_quota()

        if not quota_info:
            print("Error: Failed to retrieve storage quota information.")
            return None

        print("\n===== Google Drive Service Account Storage Quota =====\n")
        print(f"Total Quota:        {format_size(quota_info['limit'])}")
        print(
            f"Current Usage:      {format_size(quota_info['usage'])} ({quota_info['usage_percentage']:.2f}%)"
        )
        print(f"Used in Drive:      {format_size(quota_info['usage_in_drive'])}")
        print(f"Used in Trash:      {format_size(quota_info['usage_in_drive_trash'])}")
        print(f"Remaining Storage:  {format_size(quota_info['remaining'])}")
        print("\n=====================================================\n")

        if quota_info["usage_percentage"] > 80:
            print("⚠️  Warning: Your storage is running low!")
            print("This service account is running low on storage.")
            print(
                "Consider using a different service account or requesting a quota increase."
            )
            print(
                "You may need to create a new service account and update the environment variables."
            )

        return quota_info

    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def get_quota_threshold(quota_info, threshold=90.0):
    """
    Check if the storage quota usage exceeds a threshold and log appropriate messages.

    Args:
        quota_info: Dictionary containing quota information
        threshold: Percentage threshold for quota warning (default: 90.0)

    Returns:
        bool: True if quota is below threshold, False if quota exceeds threshold
    """
    if not quota_info:
        logger.error("Failed to retrieve Drive storage quota information")
        return False

    logger.info(
        f"Drive storage status: {quota_info['usage_percentage']:.2f}% used "
        f"({quota_info['usage'] / (1024 * 1024 * 1024):.2f} GB of {quota_info['limit'] / (1024 * 1024 * 1024):.2f} GB)"
    )

    if quota_info["usage_percentage"] > threshold:
        logger.error(
            f"Drive storage quota critical: {quota_info['usage_percentage']:.2f}% used "
            f"({quota_info['usage'] / (1024 * 1024 * 1024):.2f} GB of {quota_info['limit'] / (1024 * 1024 * 1024):.2f} GB). "
            "Processing halted to prevent quota exceeded errors."
        )
        logger.warning(
            "To free up space: 1) Empty trash 2) Delete unnecessary files "
            "3) Consider using a different service account"
        )
        return False

    return True


def process_file(
    drive_service, converter, file, machine_id, download_dir, output_dir, dng_folder_id
):
    """Process a single file with retry logic."""
    file_id = file["id"]
    file_name = file["name"]

    # Configuration
    MAX_RETRIES = 3  # Maximum number of retries for failed conversions

    if drive_service.is_file_uploaded(file_id):
        logger.info(f"Skipping {file_name} (ID: {file_id}), already uploaded")
        return True

    if drive_service.is_file_processed(file_id):
        logger.info(f"Skipping {file_name} (ID: {file_id}), already processed")
        return True

    status = drive_service.get_file_status(file_id)
    if status:
        retry_count = status.get("retry_count", 0)
        if status.get("status") == "failed" and retry_count >= MAX_RETRIES:
            logger.warning(
                f"Skipping {file_name} (ID: {file_id}), max retries exceeded"
            )
            return False

    if not drive_service.mark_file_as_processing(file_id, machine_id):
        logger.info(
            f"Skipping {file_name} (ID: {file_id}), already being processed by another machine"
        )
        return False

    # Download the file
    local_path = os.path.join(download_dir, file_name)
    if not drive_service.download_file(file_id, local_path):
        error_msg = f"Failed to download {file_name} (ID: {file_id})"
        logger.error(error_msg)
        drive_service.mark_file_as_failed(
            file_id=file_id, machine_id=machine_id, error_message=error_msg
        )
        return False

    logger.info(f"Downloaded: {file_name} to {local_path}")

    # Convert the file
    try:
        converted = converter.convert(
            local_path, output_dir, file_id, already_marked=True
        )
        if not converted:
            error_msg = f"Failed to convert {file_name}"
            logger.error(error_msg)
            drive_service.mark_file_as_failed(
                file_id=file_id, machine_id=machine_id, error_message=error_msg
            )
            return False

        dng_file_name = os.path.splitext(file_name)[0] + ".dng"
        dng_file_path = os.path.join(output_dir, dng_file_name)

        # Upload the converted file to Google Drive
        uploaded_id = drive_service.upload_file(dng_file_path, dng_folder_id)
        if not uploaded_id:
            error_msg = f"Failed to upload {dng_file_name} to Google Drive"
            logger.error(error_msg)
            drive_service.mark_file_as_failed(
                file_id=file_id, machine_id=machine_id, error_message=error_msg
            )
            return False

        drive_service.mark_file_as_uploaded(
            file_id,
            machine_id,
            {
                "original_filename": file_name,
                "converted_filename": dng_file_name,
                "dng_file_id": uploaded_id,
            },
        )
        return True

    except Exception as e:
        error_msg = f"Failed to process {file_name}: {str(e)}"
        logger.error(error_msg)
        drive_service.mark_file_as_failed(
            file_id=file_id, machine_id=machine_id, error_message=error_msg
        )
        return False


def clean_download_directories(base_dir=None, days_threshold=7):
    """
    Clean download and output directories if they're older than the specified threshold.

    Args:
        base_dir (str, optional): Base directory path. If None, uses ~/UCAutomation.
        days_threshold (int, optional): Number of days to keep files. Defaults to 7.

    Returns:
        tuple: (raw_cleaned, dng_cleaned) - Number of files cleaned from each directory
    """
    try:
        if not base_dir:
            home_dir = os.path.expanduser("~")
            base_dir = os.path.join(home_dir, "UCAutomation")

        download_dir = os.path.join(base_dir, "downloads/raw_files")
        output_dir = os.path.join(base_dir, "downloads/dng_files")

        marker_file = os.path.join(base_dir, ".last_cleanup")

        cleanup_needed = True
        if os.path.exists(marker_file):
            with open(marker_file, "r") as f:
                try:
                    last_cleanup = datetime.fromtimestamp(float(f.read().strip()))
                    current_time = datetime.now()

                    if last_cleanup > current_time:
                        logger.warning(
                            f"Marker file timestamp ({last_cleanup}) is in the future. Will clean directories."
                        )
                        cleanup_needed = True
                    else:
                        days_since_cleanup = (current_time - last_cleanup).days
                        if days_since_cleanup < days_threshold:
                            logger.info(
                                f"Last cleanup was {days_since_cleanup} days ago. Skipping."
                            )
                            cleanup_needed = False
                except (ValueError, OSError) as e:
                    logger.warning(
                        f"Could not read last cleanup time: {e}. Will clean directories."
                    )

        if not cleanup_needed:
            return (0, 0)

        cutoff_time = time.time() - (days_threshold * 24 * 60 * 60)

        directories = [
            {"path": download_dir, "desc": "raw files", "count": 0},
            {"path": output_dir, "desc": "DNG files", "count": 0},
        ]

        # Process directories
        for dir_info in directories:
            dir_path = dir_info["path"]
            dir_desc = dir_info["desc"]

            if os.path.exists(dir_path):
                logger.info(f"Cleaning {dir_desc} directory: {dir_path}")
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if (
                        os.path.isfile(item_path)
                        and os.path.getmtime(item_path) < cutoff_time
                    ):
                        try:
                            os.remove(item_path)
                            dir_info["count"] += 1  # Directly update the dictionary
                        except OSError as e:
                            logger.error(f"Error removing {item_path}: {e}")

        # Extract results
        raw_files_removed = directories[0]["count"]
        dng_files_removed = directories[1]["count"]

        # Update marker file with current timestamp
        with open(marker_file, "w") as f:
            f.write(str(time.time()))

        total_removed = raw_files_removed + dng_files_removed
        if total_removed > 0:
            logger.info(
                f"Cleanup complete: {raw_files_removed} raw files and {dng_files_removed} DNG files removed"
            )
        else:
            logger.info("No files needed cleanup")

        return (raw_files_removed, dng_files_removed)

    except Exception as e:
        logger.error(f"Error during directory cleanup: {e}")
        return (0, 0)


def move_to_archive(drive_service, file, archive_folder_id):
    """
    Move uploaded files from ingest folder to archive folder.

    Args:
        drive_service: Instance of GoogleDriveService class
        file (obj): File from Google Drive
        folder_id (str): The ID of the destination folder.

    Returns:
        bool: True if move was successful
    """

    file_id = file["id"]
    file_name = file["name"]

    status = drive_service.get_file_status(file_id)
    if not status or status.get("status") != "uploaded":
        logger.error(
            f"Did not move {file_name}({file_id}) to archive. Status is {status.get("status") if status else 'None'}"
        )
        return False

    try:
        drive_service.move_file(file_id, archive_folder_id)
        return True

    except Exception as e:
        logger.error(
            f"Error when trying to move {file_name}({file_id}) to archive: {str(e)}"
        )
        return False
