# Common errors

Some change

### Script doesn't have the credentials to run
- Download credentials.json
- Run the following command replacing with the proper path: export GOOGLE_CREDENTIALS_PATH="/path/to/credentials/credentials.json" 

### 404 Error when trying to upload to folder
If you get a 404 error saying that the upload folder can't be found check for a couple things
- The folder exists
- The ID in the script matches the one in the URL
- drive-automation@ucautomation.iam.gserviceaccount.com is added to "people who have access"
