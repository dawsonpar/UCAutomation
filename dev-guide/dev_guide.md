# UCAutomation - Installation Guide

## Requirements

- Mac machine
- Latest version of Adobe DNG Converter installed
- Google Drive API credentials (credentials.json file)

## 1. Download

1. Clone the repository:

```bash
git clone https://github.com/dawsonpar/UCAutomation.git
```

2. Move to your home directory:

```bash
mv UCAutomation ~/
cd ~/UCAutomation
```

## 2. Set up LaunchD for Automation

1. Move the launchd configuration file to LaunchAgents:

```bash
cp dev-guide/com.uc.rawconverter.plist ~/Library/LaunchAgents/
```

2. Edit the plist file to point to your specific Python environment and paths:

```bash
nano ~/Library/LaunchAgents/com.uc.rawconverter.plist
```

3. Change all PLACEHOLDERS in the plist file:

   - ### ProgramArguments
     - `<string>/REPLACE/PLACEHOLDER/UCAutomation/dev-guide/uc_automation</string>` change /REPLACE/PLACEHOLDER/path/to with actual path to /UCAutomation directory
   - ### StandardOutPath

     - `<string>/REPLACE/PLACEHOLDER/UCAutomation/src/lib/rawconverter_out.log</string>` change /REPLACE/PLACEHOLDER/path/to with actual path to /UCAutomation directory

   - ### StandardErrorPath

     - `<string>/REPLACE/PLACEHOLDER/UCAutomation/src/lib/rawconverter_out.log</string>` change /REPLACE/PLACEHOLDER/path/to with actual path to /UCAutomation directory

   - ### EnvironmentVariables
     - Change strings for GOOGLE_CREDENTIALS_PATH and FIREBASE_CREDENTIALS_PATH to the path for your Google Drive API credentials.
     - NAS Variables: Change strings to valid IP, port, username, password, and final DNG destination path.
     - Change strings for INGEST_FOLDER_ID and ARCHIVE_FOLDER_ID to google drive folder IDs for 'ingest' and 'already ingested'.

4. Load and start the LaunchD service:

```bash
launchctl load ~/Library/LaunchAgents/com.uc.rawconverter.plist
launchctl start com.uc.rawconverter
```

## 3. Verify Installation

1. Check the logs to verify the script is running:

```bash
cat ~/UCAutomation/lib/rawconverter_out.log
```

2. Check for errors:

```bash
cat ~/UCAutomation/lib/rawconverter_error.log
```

3. Check if LaunchD file is running:

```bash
launchctl list | grep rawconverter
```

To stop the script run the following command:

```bash
launchctl unload ~/Library/LaunchAgents/com.uc.rawconverter.plist
```

## Troubleshooting

### Creating a new Google IAM Service Account

Navigate to Google Cloud and go into the UCAutomation project.

In the sidebar go to IAM & Admin and Service Accounts
<img width="963" alt="Screenshot 2025-04-28 at 10 38 00 AM" src="https://github.com/user-attachments/assets/29b59f82-65ab-431e-abc6-fca2b6f76298" />

Click on "Create service account."
<img width="1800" alt="Screenshot 2025-04-28 at 10 39 17 AM" src="https://github.com/user-attachments/assets/f42ba82e-6a0d-45c4-866f-2d4dad2ef66f" />

Give the Service Account a descriptive name that can identify your machine
<img width="947" alt="Screenshot 2025-04-28 at 10 42 15 AM" src="https://github.com/user-attachments/assets/ef4c460d-5ee5-4c57-893c-c597287b7157" />

Give the Service account the following roles: Firebase Rules System, Firestore Service Agent, Cloud Datastore User
<img width="947" alt="Screenshot 2025-04-28 at 10 42 59 AM" src="https://github.com/user-attachments/assets/a956ffa6-0267-4363-8150-19fa769faa5c" />

Click Done and then click on the email of the service account you just created. Navigate to Keys and click on Add key.
<img width="670" alt="Screenshot 2025-06-04 at 11 43 25 AM" src="https://github.com/user-attachments/assets/1904300b-0e26-4ab0-a369-be16a163a784" />

Create a new key and select JSON for the format of your key.
<img width="888" alt="Screenshot 2025-06-04 at 11 44 41 AM" src="https://github.com/user-attachments/assets/fa3524e8-1cee-446a-9021-4fa96941e257" />

Once you click create the service account key will be downloaded to your computer. Rename this file to something appropriate like `{machine}-credentials.json` then move it to the root directory of the UCAutomation project.

Don't forget to update the path to this credentials file in your launchd file.
<img width="888" alt="Screenshot 2025-06-04 at 11 50 19 AM" src="https://github.com/user-attachments/assets/943bb59d-5c3c-402c-8fa1-38f9011bee72" />

### Synology NAS Failed to establish a new connection: [Errno 65] No route to host
Make sure that you give the exec file/launchd file permission to access machines on your local network.

### 407 error when trying to upload to Synology NAS
Validate that the Synology user has permission to upload or edit in the Synology destination folder.

### 408 error when trying to upload to Synology NAS
Validate that the Synology destination folder path is correct and exists.

### Converted file not found

Check the version of Adobe DNG Converter and see if it supports converting the latest raw photos. You may need to redownload the latest version of Adobe DNG Converter.

### No such file or directory: 'Users/{User}/UCAutomation/lib/rawconverter_out.log'

- Ensure you've created the lib directory as described in step 4.

### Script doesn't have the credentials to run

- Verify your credentials.json file exists and the path in .env is correct

### 404 Error when trying to upload to Google Drive folder

If you get a 404 error about the upload folder, check for:

- The folder exists in Google Drive
- The folder ID in the .env file matches the one in the URL
- The service account email (`drive-automation@ucautomation.iam.gserviceaccount.com`) has been added to "people who have access" for both folders

### LaunchD service not running

- Check the status with: `launchctl list | grep com.uc.rawconverter`
- Examine the log files for errors
- Try unloading and reloading the service:

```bash
launchctl unload ~/Library/LaunchAgents/com.uc.rawconverter.plist
launchctl load ~/Library/LaunchAgents/com.uc.rawconverter.plist
launchctl start com.uc.rawconverter
```
