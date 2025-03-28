# How to install
### Requirements
- Must run on a Mac machine
- Pyenv must be installed with python >= 3.13.1
- Adobe DNG Converter must be installed

### 1. Download this repo

Clone or download this repo onto the designated machine.

Rename the project folder to UCAutomation and move it to the current user's directory (e.g. ~/Users/photographer/UCAutomation).


# Common errors

### Script doesn't have the credentials to run
- Download credentials.json
- Run the following command replacing with the proper path: export GOOGLE_CREDENTIALS_PATH="/path/to/credentials/credentials.json" 

### 404 Error when trying to upload to folder
If you get a 404 error saying that the upload folder can't be found check for a couple things
- The folder exists
- The ID in the script matches the one in the URL
- drive-automation@ucautomation.iam.gserviceaccount.com is added to "people who have access"
