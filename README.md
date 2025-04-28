# UCAutomation

https://github.com/user-attachments/assets/e391ddd0-df56-483e-9acd-44d399f5814b

## Description
Automate the hourly conversion of new raw photos (.arw, .nef, .cr3) uploaded to a specific Google Drive folder to .dng format.

## DEVELOPER GUIDE

[dev_guide](https://github.com/dawsonpar/UCAutomation/blob/main/dev_guide.md)

### Functional Requirements

- [ ] Monitor Google Drive folder for new raw photos every hour using Google Drive API
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

## Architecture

- A python script will be scheduled to run hourly
- The script will use the Google Drive API to interact with Google Drive
- Image conversion will be handled by Adobe DNG Converter
- Google Firestore is used to track file processing status across multiple machines

### Data Flow

1. Hourly schedule triggers the Python script
2. Google Drive Monitor retrieves file list and identifies new files
3. Each file is marked as "processing" in Firestore by the current machine
4. Raw to DNG Converter converts new files to .dng
5. Google Drive Uploader uploads .dng files to the destination folder
6. Files are marked as "processed" in Firestore
7. Logger logs all actions

## Setup

### Prerequisites

- Python 3.7+
- pip
- Adobe DNG Converter installed (Mac)
- Google Cloud project with Drive API and Firestore enabled

### Environment Variables

The following environment variables must be set:

```
GOOGLE_CREDENTIALS_PATH=/path/to/google-drive-credentials.json
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
INGEST_FOLDER_ID=your_google_drive_folder_id
DNG_FOLDER_ID=your_destination_folder_id
```

### Installation

1. Clone the repository
2. Install the required packages: `pip install -r src/requirements.txt`
3. Set up the environment variables
4. Run the script: `python src/main.py`

## Multi-machine Processing

This application supports processing files across multiple machines by using Google Firestore to track file status. Each machine will:

1. Check if a file is already processed in Firestore
2. Try to mark a file as "processing" with its machine ID
3. Skip files that are already being processed by other machines
4. Mark files as "processed" when complete
5. Store additional metadata about each processed file
