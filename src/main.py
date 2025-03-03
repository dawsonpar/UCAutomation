import os

from google_drive_service import GoogleDriveService


def main():
    folder_id = "1p6i00JY5lnYBzapVSKHtyd5IRFABuSTA"
    processed_files_path = "src/processed_files.json"
    drive_service = GoogleDriveService(folder_id, processed_files_path)
    files = drive_service.list_files()

    if files:
        print("Files in Google Drive folder:")
        for file in files:
            print(f"- {file['name']} (ID: {file['id']})")
    else:
        print("No files found in Google Drive folder.")


if __name__ == "__main__":
    main()
