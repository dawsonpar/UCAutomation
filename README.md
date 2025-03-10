# UCAutomation

## Description
Automate the hourly conversion of new raw photos (.arw, .nef, .cr3) uploaded to a specific Google Drive folder to .dng format.

## DEVELOPER GUIDE
[dev_guide](https://github.com/dawsonpar/UCAutomation/blob/main/dev_guide.md)

### Functional Requirements
- [ ] Monitor Google Drive folder for new raw photos every hour using Google Drive API
- [ ] Identify new files: determine which files are new since the last check
- [x] Convert raw files (.cr3, .arw, .nef) into .dng
- [x] Log operations and errors.

### Non-functional Requirements
- Minimal downtime
- System should handle increasing volumes of photos
- Codebase should be easy to maintain and well documented.
- Manage Google Drive API credentials securely.
- Handle errors and provide informative logs.

## Architecture
- A python script will be scheduled to run hourly
- The script will use the Google Drive API to interact with Google Drive
- Image conversion will be handled by a Adobe DNG Converter

### Data Flow
1. Hourly schedule triggers the Python script.
2. Google Drive Monitor retrieves file list and identifies new files.
3. Raw to DNG Converter converts new files to .dng.
4. Google Drive Uploader uploads .dng files to the destination folder.
5. Logger logs all actions.
6. The timestamp of processed files is stored.
