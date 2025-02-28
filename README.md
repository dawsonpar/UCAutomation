# UCAutomation

## Description
Automate the hourly conversion of new raw photos (.arw, .nef, .cr3) uploaded to a specific Google Drive folder to .dng format.


### Functional Requirements
- [ ] Monitor Google Drive folder for new raw photos every hour using Google Drive API
- [ ] Identify new files: determine which files are new since the last check
- [ ] Convert raw files (.cr3, .arw, .nef) into .dng
- [ ] Log operations and errors.
- [ ] Prevent duplicate file processing.

### Non-functional Requirements
- Minimal downtime
- System should handle increasing volumes of photos
- Codebase should be easy to maintain and well documented.
- Manage Google Drive API credentials securely.
- Handle errors and provide informative logs.

## Architecture
- A python script will be scheduled to run hourly
- The script will use the Google Drive API to interact with Google Drive
- Image conversion will be handled by a combination of rawpy and exiftool.

### Data Flow
1. Hourly schedule triggers the Python script.
2. Google Drive Monitor retrieves file list and identifies new files.
3. Raw to DNG Converter converts new files to .dng.
4. Google Drive Uploader uploads .dng files to the destination folder.
5. Logger logs all actions.
6. The timestamp of processed files is stored.
