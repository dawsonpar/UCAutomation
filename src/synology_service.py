import os
import shutil

import requests

from firestore_service import FirestoreService
from log_config import get_logger

logger = get_logger()


class SynologyService:
    def __init__(
        self, fire_base_credentials_path=None, collection_name="processed_files"
    ):
        self.firestore_service = FirestoreService(
            collection_name=collection_name,
            credentials_path=fire_base_credentials_path,
        )

    def get_api_info(self, base_url):
        """
        Returns available APIs. Change query to "all" to see all available APIs.
        """
        try:

            info_url = f"{base_url}/query.cgi"
            params_info = {
                "api": "SYNO.API.Info",
                "version": "1",
                "method": "query",
                "query": "SYNO.API.Auth,SYNO.FileStation.List, SYNO.FileStation.Upload",
            }
            response = requests.get(info_url, params=params_info, verify=False)
            return response.json()
        except Exception as e:
            logger.info(f"Error when trying to get API info: {str(e)}")
            return None

    def get_sid(self, base_url, username, password):
        try:
            auth_url = f"{base_url}/auth.cgi"
            params_auth = {
                "api": "SYNO.API.Auth",
                "version": "6",
                "method": "login",
                "account": username,
                "passwd": password,
                "session": "FileStation",
                "format": "sid",
            }
            response = requests.get(auth_url, params=params_auth, verify=False)
            data = response.json()

            if data.get("success"):
                sid = data["data"]["sid"]
                return sid
            else:
                logger.error("Login failed:", data)
                return data

        except Exception as e:
            logger.error(f"Error when trying to get session ID: {str(e)}")
            return None

    def list_shares(self, base_url, sid):
        try:
            list_url = f"{base_url}/entry.cgi"
            params_list = {
                "api": "SYNO.FileStation.List",
                "version": "2",
                "method": "list_share",
                "_sid": sid,
            }
            response = requests.get(list_url, params=params_list, verify=False)
            return response.json()

        except Exception as e:
            logger.error(f"Error when trying to list shares from FileStation: {str(e)}")
            return None

    def logout(self, base_url, sid):
        try:
            auth_url = f"{base_url}/auth.cgi"
            params_logout = {
                "api": "SYNO.API.Auth",
                "version": "2",
                "method": "logout",
                "session": "FileStation",
                "_sid": sid,
            }
            requests.get(auth_url, params=params_logout, verify=False)
            return True

        except Exception as e:
            logger.error(f"Error when trying to logout: {str(e)}")
            return False
