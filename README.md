# UCAutomation

https://github.com/user-attachments/assets/e391ddd0-df56-483e-9acd-44d399f5814b

## Description
Automate the hourly conversion of new raw photos (.arw, .nef, .cr3) uploaded to a specific Google Drive folder to .dng format.

## DEVELOPER GUIDE

[How to install and set up](https://github.com/dawsonpar/UCAutomation/blob/main/dev-guide/dev_guide.md)

### Functional Requirements

- [x] Monitor Google Drive folder for new raw photos every hour using launchd
- [x] Identify new files: determine which files are new since the last check
- [x] Convert raw files (.cr3, .arw, .nef) into .dng
- [x] Log operations and errors
- [x] Prevent duplicate processing across multiple machines
- [x] Track file status in Google Firestore

### Non-functional Requirements

- Minimal downtime
- System should handle increasing volumes of photos
- Codebase should be easy to maintain and well documented
- Manage Google Drive API credentials securely
- Handle errors and provide informative logs

### Limits
- Google Service Accounts have an upload limit of 15GB

## Architecture

- A python script will be scheduled to run hourly
- The script will use the Google Drive API to interact with Google Drive
- Image conversion will be handled by Adobe DNG Converter
- Google Firestore is used to track file processing status across multiple machines

### Data Flow

1. Hourly launchd plist file triggers the Python script
2. GoogleDriveService retrieves Ingest folder file list and identifies new raw photos
3. Each file is marked as "processing" in Firestore by the current machine
4. Rawconverter converts new raw photos to DNG format
5. GoogleDriveService uploads DNG files to the destination folder (Converted)
6. Files are marked as "processed" in Firestore
7. Logger logs all actions

### Multi-machine Processing

This application supports processing files across multiple machines by using Google Firestore to track file status. Each machine will:

1. Check if a file is already processed in Firestore
2. Try to mark a file as "processing" with its machine ID
3. Skip files that are already being processed by other machines
4. Mark files as "processed" when complete
5. Store additional metadata about each processed file
