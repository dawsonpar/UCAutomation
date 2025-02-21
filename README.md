# UCAutomation

## Description
Using the Google Drive API this Raw Conversion Automation will detect when a new raw file has been added to a selected folder.
Then the raw photo will be converted to DNG.
This will loop until all raw photos in the folder have been converted.

### Functional Requirements
- Detect addition of files inside of a directory from Google Drive using Google Drive API
- Convert raw files (.cr3, .arw, .nef) into .dng

### Non-functional Requirements
- We do not want to delete the raw files

### Stretch Features
- Send email notification about files being converted
