#!/usr/bin/env python3
"""
Script to check and display Google Drive quota for a service account
"""

import logging
import os
import sys

from dotenv import load_dotenv

from google_drive_service import GoogleDriveService


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


def main():
    # Load environment variables
    load_dotenv()

    # Get required environment variables
    folder_id = os.environ.get("INGEST_FOLDER_ID")
    google_creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH")
    firebase_creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")

    # Validate required environment variables
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
        sys.exit(1)

    try:
        # Initialize Google Drive service
        drive_service = GoogleDriveService(
            folder_id=folder_id,
            credentials_path=google_creds_path,
            firebase_credentials_path=firebase_creds_path,
        )

        # Get storage quota
        quota_info = drive_service.get_storage_quota()

        if not quota_info:
            print("Error: Failed to retrieve storage quota information.")
            sys.exit(1)

        # Print quota information in a readable format
        print("\n===== Google Drive Service Account Storage Quota =====\n")
        print(f"Total Quota:        {format_size(quota_info['limit'])}")
        print(
            f"Current Usage:      {format_size(quota_info['usage'])} ({quota_info['usage_percentage']:.2f}%)"
        )
        print(f"Used in Drive:      {format_size(quota_info['usage_in_drive'])}")
        print(f"Used in Trash:      {format_size(quota_info['usage_in_drive_trash'])}")
        print(f"Remaining Storage:  {format_size(quota_info['remaining'])}")
        print("\n=====================================================\n")

        # Additional tips if storage is running low
        if quota_info["usage_percentage"] > 80:
            print("⚠️  Warning: Your storage is running low!")
            print("Tips to free up space:")
            print("1. Empty your trash (files in trash still count toward quota)")
            print("2. Remove unnecessary files from Drive")
            print(
                "3. Consider using a different service account or requesting a quota increase"
            )
            print(
                "4. Review large files by visiting: https://drive.google.com/drive/quota"
            )
            print("\n")

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
