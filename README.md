# UCAutomation

https://github.com/user-attachments/assets/38a12943-da1d-40ff-86d0-fa03b2ca2cfc

## Description
The UC Rawconverter is a software that automates the process of converting raw photos (.cr3, .arw, .nef) from Google Drive into Adobe DNG format and uploads the converted file to Synology.

Users will upload their raw photos to a specified “ingest” Google Drive folder. Then, some Mac machines using launchd will periodically check this folder for unprocessed raw photos. Once they find raw photos, they will download the photos, convert them, and then upload them to Synology. Once a photo is uploaded, the original photo in the “ingest” folder will be moved to a specified “archive” folder.


## DEVELOPER GUIDE
[UC Rawconverter Design Document](https://docs.google.com/document/d/1-xYYRrNgQMpPOd9bhLKtG6waozlBhw3YML_8DNn-l8A/edit?usp=sharing)

[How to install and set up](https://github.com/dawsonpar/UCAutomation/blob/main/dev-guide/dev_guide.md)

