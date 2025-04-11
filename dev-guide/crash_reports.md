# Report of Failures and Remedies

[comment]: <> (Format <Date> Title of Error)
[comment]: <> (Description)

## 2025-04-11 Quota Limit on Google Service Account
Google service accounts have a default storage limit of 15GB. Currently trying to find a workaround or a way to increase the limit.

Currently, as a hotfix, I'm manually creating a new service account in Google Cloud and changing the credentials on the machine running the drive automation.
