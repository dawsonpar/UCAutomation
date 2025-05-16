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
