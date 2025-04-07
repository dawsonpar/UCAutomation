# UCAutomation - Installation Guide

## Requirements

- Mac machine
- Pyenv installed
- Python >= 3.13.1
- Adobe DNG Converter 17.2.0 installed
- Google Drive API credentials (credentials.json file)

## 1. Download and Setup

1. Clone the repository:

```bash
git clone https://github.com/dawsonpar/UCAutomation.git
```

2. Move to your home directory:

```bash
mv UCAutomation ~/
cd ~/UCAutomation
```

## 2. Set up Python Environment

1. Install pyenv if not already installed:

```bash
brew install pyenv
```

2. Install pyenv-virtualenv if not already installed:

```bash
brew install pyenv-virtualenv
```

3. Add pyenv to your shell:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
```

4. Restart your terminal or run:

```bash
source ~/.zshrc
```

5. Install Python using pyenv:

```bash
pyenv install 3.13.1
```

6. Create and activate a virtual environment:

```bash
pyenv virtualenv 3.13.1 ucauto
pyenv local ucauto
```

## 3. Install Dependencies

```bash
pip install -r src/requirements.txt
```
or
```bash
pip3 install -r src/requirements.txt
```


## 4. Create Required Directories

Create the lib directory for logs:

```bash
mkdir -p ~/UCAutomation/lib
mkdir -p ~/UCAutomation/downloads/raw_files
mkdir -p ~/UCAutomation/downloads/dng_files
```

## 5. Configure Environment Variables

1. Create or edit the .env file in the root directory:

```bash
touch .env
```

2. Add the following content to the .env file (replace the placeholders with your actual values):

```
# Google Service Account Credentials Path
GOOGLE_CREDENTIALS_PATH="/replace/path/to/UCAutomation/credentials.json"
FIREBASE_CREDENTIALS_PATH="/replace/path/to/credentials.json"

# Google Drive IDs
INGEST_FOLDER_ID="your_ingest_folder_id_here"
DNG_FOLDER_ID="your_dng_folder_id_here"
```

3. Place your credentials.json file in the root directory of the project.

## 6. Set up LaunchD for Automation

1. Move the launchd configuration file to LaunchAgents:

```bash
cp dev-guide/com.uc.rawconverter.plist ~/Library/LaunchAgents/
```

2. Edit the plist file to point to your specific Python environment and paths:

```bash
nano ~/Library/LaunchAgents/com.uc.rawconverter.plist
```

3. Update the following in the plist file:

   - `<string>/Library/Frameworks/Python.framework/Versions/3.12/bin/python3</string>` with your pyenv Python path. Find your path with `which python` after activating your virtualenv.
   - `<string>/Users/photographer/UCAutomation/src/main.py</string>` with your actual path to main.py
   - Update any other paths to match your username and setup

4. Load and start the LaunchD service:

```bash
launchctl load ~/Library/LaunchAgents/com.uc.rawconverter.plist
launchctl start com.uc.rawconverter
```

## 7. Verify Installation

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

## Troubleshooting

### Converted file not found

Check the version of Adobe DNG Converter and see if it supports converting the latest raw photos. You may need to redownload the latest version of Adobe DNG Converter.

### No such file or directory: 'Users/{User}/UCAutomation/lib/rawconverter_out.log'

- Ensure you've created the lib directory as described in step 4.

### Script doesn't have the credentials to run

- Verify your credentials.json file exists and the path in .env is correct

### 404 Error when trying to upload to folder

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
