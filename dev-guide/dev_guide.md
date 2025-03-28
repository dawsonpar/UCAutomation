# How to install
### Requirements
- Must run on a Mac machine
- Pyenv must be installed with python >= 3.13.1
- Adobe DNG Converter must be installed

### 1. Download this repo

Clone or download this repo onto the designated machine.

Rename the project folder to UCAutomation and move it to the current user's directory (e.g. ~/Users/photographer/UCAutomation).

### 2. Move the launchd file into LaunchAgents

Inside of the dev-guide folder there is a launchd plist file that needs to be moved to ~/Library/LaunchAgents

A simple way to move the file here is to open the terminal and run the command
```
cd Library/LaunchAgents/ && open .
```

This will open a finder window inside of the LaunchAgents folder. Now drag the file `com.uc.rawconverter.plist` into the LaunchAgents folder.

### 3. Set up pyenv
Open a terminal window and navigate to the UCAutomation folder (if in the correct spot it should be /Users/{myUser}/UCAutomation)

Run the command `pyenv version`

If it says version x is not installed then go ahead and run the command 
```
pyenv install {x}
```

Once installed run the command `pyenv local {x}`

Install pyenv-virtualenv if not already downloaded using 
```
brew install pyenv-virtualenv
```

Now create and use an isolated virtual environment by running the commands
```
pyenv virtualenv 3.13.1 ucauto
pyenv local ucauto
```
The virtualenv name ucauto can be changed to your liking

### 4. Install dependencies
In the terminal navigate to the UCAutomation folder and run the following command
```
pip3 install -r src/requirements.txt
```

# Common errors

### Script doesn't have the credentials to run
- Download credentials.json
- Run the following command replacing with the proper path: export GOOGLE_CREDENTIALS_PATH="/path/to/credentials/credentials.json" 

### 404 Error when trying to upload to folder
If you get a 404 error saying that the upload folder can't be found check for a couple things
- The folder exists
- The ID in the script matches the one in the URL
- drive-automation@ucautomation.iam.gserviceaccount.com is added to "people who have access"
