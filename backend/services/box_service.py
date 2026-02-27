
import os
import logging
from box_sdk_gen import BoxClient, BoxDeveloperTokenAuth, BoxOAuth
from box_sdk_gen.schemas import FileFull, FolderFull
from config import settings

logger = logging.getLogger(__name__)

class BoxService:
    """
    Service to handle Box API authentication and file operations.
    Designed for READ-ONLY access to Box. Does not perform any write/delete/update operations on Box files or folders.
    """
    def __init__(self):
        self.client = None

    def get_client(self):
        """
        Authenticate with Box using Developer Token or OAuth (Client Credentials).
        """
        if self.client:
            return self.client
            
        # Try Developer Token first (simplest for testing)
        developer_token = settings.BOX_DEVELOPER_TOKEN
        if developer_token:
            auth = BoxDeveloperTokenAuth(token=developer_token)
            self.client = BoxClient(auth=auth)
            logger.info("Authenticated with Box using Developer Token")
            return self.client

        # Fallback to Client Credentials (JWT or CC) if configured
        client_id = settings.BOX_CLIENT_ID
        client_secret = settings.BOX_CLIENT_SECRET
        enterprise_id = settings.BOX_ENTERPRISE_ID
        
        if client_id and client_secret:
             # This is a simplified example. For real OAuth/CC, you'd use BoxCCAuth
             # But for now, let's stick to Developer Token as primary or simple OAuth if token provided
             logger.warning("Box Client ID/Secret found but full OAuth flow not implemented in this snippet. Please use Developer Token for quick testing.")
             pass
        
        if not self.client:
            raise ValueError("No valid Box credentials found. Please set BOX_DEVELOPER_TOKEN in .env")
            
        return self.client

    def list_folder_items(self, folder_id: str):
        """
        List items in a Box folder.
        """
        client = self.get_client()
        try:
            items = client.folders.get_folder_items(folder_id)
            return items.entries
        except Exception as e:
            logger.error(f"Error listing folder {folder_id}: {e}")
            raise

    def find_folder_by_name(self, parent_folder_id: str, folder_name: str):
        """
        Find a specific folder by name within a parent folder.
        """
        items = self.list_folder_items(parent_folder_id)
        for item in items:
            if item.type == 'folder' and item.name == folder_name:
                return item
        return None
        
    def download_file(self, file_id: str, destination_path: str):
        """
        Download a file from Box to a local path.
        """
        client = self.get_client()
        try:
            download_stream = client.downloads.download_file(file_id)
            if not download_stream:
                 raise Exception("Download returned no content stream")
                 
            with open(destination_path, 'wb') as file_stream:
                import shutil
                shutil.copyfileobj(download_stream, file_stream)
                
            logger.info(f"Downloaded file {file_id} to {destination_path}")
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise

box_service = BoxService()
