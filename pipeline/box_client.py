"""
Box API Client

Purpose: Interface with Box Content Cloud for bill storage and retrieval
"""

import os
from pathlib import Path
from typing import Optional, List, Dict
import logging
from boxsdk import Client, OAuth2, JWTAuth
from boxsdk.exception import BoxAPIException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BoxClient:
    """Client for interacting with Box API."""
    
    def __init__(self, auth_type: str = "jwt"):
        """
        Initialize Box client.
        
        Args:
            auth_type: "jwt" or "oauth"
        """
        self.client = None
        self.auth_type = auth_type
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Box client with authentication."""
        try:
            if self.auth_type == "jwt":
                # JWT authentication (for service accounts)
                client_id = os.getenv("BOX_CLIENT_ID")
                client_secret = os.getenv("BOX_CLIENT_SECRET")
                enterprise_id = os.getenv("BOX_ENTERPRISE_ID")
                jwt_key_path = os.getenv("BOX_JWT_PRIVATE_KEY_PATH")
                
                if not all([client_id, client_secret, enterprise_id, jwt_key_path]):
                    logger.warning("Box JWT credentials not found. Box integration disabled.")
                    return
                
                auth = JWTAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    enterprise_id=enterprise_id,
                    jwt_key_id=os.getenv("BOX_JWT_KEY_ID", ""),
                    rsa_private_key_file_sys_path=jwt_key_path,
                    rsa_private_key_passphrase=os.getenv("BOX_JWT_PASSPHRASE", "")
                )
                access_token = auth.authenticate_instance()
                self.client = Client(auth)
                
            elif self.auth_type == "oauth":
                # OAuth2 authentication (for user accounts)
                client_id = os.getenv("BOX_CLIENT_ID")
                client_secret = os.getenv("BOX_CLIENT_SECRET")
                
                if not all([client_id, client_secret]):
                    logger.warning("Box OAuth credentials not found. Box integration disabled.")
                    return
                
                oauth = OAuth2(
                    client_id=client_id,
                    client_secret=client_secret,
                    access_token=os.getenv("BOX_ACCESS_TOKEN", "")
                )
                self.client = Client(oauth)
            
            logger.info("Box client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Box client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Box client is available."""
        return self.client is not None
    
    def download_bill_from_box(self, folder_id: str, filename: str, output_path: str) -> bool:
        """
        Download a bill PDF from Box folder.
        
        Args:
            folder_id: Box folder ID
            filename: Name of the file to download
            output_path: Local path to save the file
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Box client not available")
            return False
        
        try:
            # Get folder
            folder = self.client.folder(folder_id=folder_id).get()
            
            # Find file
            items = folder.get_items()
            file_item = None
            for item in items:
                if item.name == filename:
                    file_item = item
                    break
            
            if not file_item:
                logger.error(f"File {filename} not found in folder {folder_id}")
                return False
            
            # Download file
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "wb") as f:
                file_item.download_to(f)
            
            logger.info(f"Downloaded {filename} to {output_path}")
            return True
            
        except BoxAPIException as e:
            logger.error(f"Box API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    def upload_output_to_box(self, file_path: str, folder_id: str, file_name: Optional[str] = None) -> bool:
        """
        Upload CSV/JSON output to Box folder.
        
        Args:
            file_path: Local path to file
            folder_id: Box folder ID
            file_name: Optional custom filename (defaults to original filename)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.error("Box client not available")
            return False
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            if file_name is None:
                file_name = file_path_obj.name
            
            # Get folder
            folder = self.client.folder(folder_id=folder_id).get()
            
            # Upload file
            with open(file_path, "rb") as f:
                uploaded_file = folder.upload_stream(f, file_name)
            
            logger.info(f"Uploaded {file_name} to Box folder {folder_id}")
            return True
            
        except BoxAPIException as e:
            logger.error(f"Box API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False
    
    def list_bills_in_folder(self, folder_id: str) -> List[Dict]:
        """
        Get list of available bills in a Box folder.
        
        Args:
            folder_id: Box folder ID
        
        Returns:
            List of file metadata dicts
        """
        if not self.is_available():
            logger.error("Box client not available")
            return []
        
        try:
            folder = self.client.folder(folder_id=folder_id).get()
            items = folder.get_items()
            
            bills = []
            for item in items:
                if item.type == "file" and item.name.endswith(".pdf"):
                    bills.append({
                        "id": item.id,
                        "name": item.name,
                        "size": item.size,
                        "modified_at": item.modified_at.isoformat() if item.modified_at else None
                    })
            
            logger.info(f"Found {len(bills)} bills in folder {folder_id}")
            return bills
            
        except BoxAPIException as e:
            logger.error(f"Box API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    def get_box_ai_summary(self, file_id: str) -> Optional[str]:
        """
        Use Box AI to generate bill summary (optional feature).
        
        Note: This requires Box AI API access which may not be available in all plans.
        
        Args:
            file_id: Box file ID
        
        Returns:
            AI-generated summary string, or None if unavailable
        """
        if not self.is_available():
            logger.error("Box client not available")
            return None
        
        try:
            # Box AI integration would go here
            # This is a placeholder - actual implementation depends on Box AI API availability
            logger.warning("Box AI summary not yet implemented")
            return None
            
        except Exception as e:
            logger.error(f"Error getting Box AI summary: {e}")
            return None


def initialize_box_client(auth_type: str = "jwt") -> BoxClient:
    """
    Initialize and return Box client.
    
    Args:
        auth_type: "jwt" or "oauth"
    
    Returns:
        BoxClient instance
    """
    return BoxClient(auth_type=auth_type)


if __name__ == "__main__":
    # Test Box client
    client = initialize_box_client()
    if client.is_available():
        print("Box client initialized successfully")
    else:
        print("Box client not available (credentials not configured)")

