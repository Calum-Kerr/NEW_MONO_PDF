"""
Cloud storage integration module.
Provides integration with Google Drive, Dropbox, OneDrive, and other cloud storage providers.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
import requests
from urllib.parse import urlencode

@dataclass
class CloudFile:
    """Represents a file in cloud storage."""
    file_id: str
    name: str
    size: int
    mime_type: str
    provider: str
    download_url: Optional[str]
    web_view_url: Optional[str]
    thumbnail_url: Optional[str]
    modified_time: datetime
    created_time: datetime
    parent_folder_id: Optional[str]
    is_folder: bool
    metadata: Dict[str, Any]

@dataclass
class CloudFolder:
    """Represents a folder in cloud storage."""
    folder_id: str
    name: str
    provider: str
    parent_folder_id: Optional[str]
    web_view_url: Optional[str]
    created_time: datetime
    modified_time: datetime
    file_count: int
    metadata: Dict[str, Any]

class CloudStorageProvider(ABC):
    """Abstract base class for cloud storage providers."""
    
    @abstractmethod
    def authenticate(self, access_token: str) -> bool:
        """Authenticate with the cloud storage provider."""
        pass
    
    @abstractmethod
    def list_files(self, folder_id: str = None, file_type: str = None) -> List[CloudFile]:
        """List files in a folder."""
        pass
    
    @abstractmethod
    def upload_file(self, file_path: str, folder_id: str = None, name: str = None) -> CloudFile:
        """Upload a file to cloud storage."""
        pass
    
    @abstractmethod
    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download a file from cloud storage."""
        pass
    
    @abstractmethod
    def get_file_info(self, file_id: str) -> CloudFile:
        """Get file information."""
        pass
    
    @abstractmethod
    def create_folder(self, name: str, parent_folder_id: str = None) -> CloudFolder:
        """Create a new folder."""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete a file."""
        pass

class GoogleDriveProvider(CloudStorageProvider):
    """Google Drive integration provider."""
    
    def __init__(self):
        self.access_token = None
        self.api_base = "https://www.googleapis.com/drive/v3"
        self.upload_base = "https://www.googleapis.com/upload/drive/v3"
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self, access_token: str) -> bool:
        """Authenticate with Google Drive."""
        self.access_token = access_token
        
        # Test authentication
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{self.api_base}/about?fields=user", headers=headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Google Drive authentication failed: {str(e)}")
            return False
    
    def list_files(self, folder_id: str = None, file_type: str = None) -> List[CloudFile]:
        """List files in Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Build query
            query_parts = []
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            if file_type:
                if file_type == "pdf":
                    query_parts.append("mimeType='application/pdf'")
                elif file_type == "document":
                    query_parts.append("mimeType contains 'document' or mimeType contains 'text'")
            
            query_parts.append("trashed=false")
            query = " and ".join(query_parts)
            
            params = {
                "q": query,
                "fields": "files(id,name,size,mimeType,webViewLink,thumbnailLink,modifiedTime,createdTime,parents)"
            }
            
            response = requests.get(f"{self.api_base}/files", headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                files = []
                
                for item in data.get("files", []):
                    cloud_file = CloudFile(
                        file_id=item["id"],
                        name=item["name"],
                        size=int(item.get("size", 0)),
                        mime_type=item["mimeType"],
                        provider="google_drive",
                        download_url=None,  # Will be generated on demand
                        web_view_url=item.get("webViewLink"),
                        thumbnail_url=item.get("thumbnailLink"),
                        modified_time=datetime.fromisoformat(item["modifiedTime"].replace("Z", "+00:00")),
                        created_time=datetime.fromisoformat(item["createdTime"].replace("Z", "+00:00")),
                        parent_folder_id=item.get("parents", [None])[0],
                        is_folder=item["mimeType"] == "application/vnd.google-apps.folder",
                        metadata=item
                    )
                    files.append(cloud_file)
                
                return files
            else:
                self.logger.error(f"Failed to list files: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing Google Drive files: {str(e)}")
            return []
    
    def upload_file(self, file_path: str, folder_id: str = None, name: str = None) -> CloudFile:
        """Upload file to Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # File metadata
            metadata = {
                "name": name or os.path.basename(file_path)
            }
            if folder_id:
                metadata["parents"] = [folder_id]
            
            # Upload file
            with open(file_path, 'rb') as file:
                files = {
                    'metadata': (None, json.dumps(metadata), 'application/json'),
                    'media': (metadata["name"], file, 'application/octet-stream')
                }
                
                response = requests.post(
                    f"{self.upload_base}/files?uploadType=multipart&fields=id,name,size,mimeType,webViewLink,createdTime,modifiedTime",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    files=files
                )
            
            if response.status_code == 200:
                data = response.json()
                return CloudFile(
                    file_id=data["id"],
                    name=data["name"],
                    size=int(data.get("size", 0)),
                    mime_type=data["mimeType"],
                    provider="google_drive",
                    download_url=None,
                    web_view_url=data.get("webViewLink"),
                    thumbnail_url=None,
                    modified_time=datetime.fromisoformat(data["modifiedTime"].replace("Z", "+00:00")),
                    created_time=datetime.fromisoformat(data["createdTime"].replace("Z", "+00:00")),
                    parent_folder_id=folder_id,
                    is_folder=False,
                    metadata=data
                )
            else:
                raise Exception(f"Upload failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error uploading to Google Drive: {str(e)}")
            raise
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download file from Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.api_base}/files/{file_id}?alt=media", headers=headers)
            
            if response.status_code == 200:
                with open(local_path, 'wb') as file:
                    file.write(response.content)
                return True
            else:
                self.logger.error(f"Failed to download file: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading from Google Drive: {str(e)}")
            return False
    
    def get_file_info(self, file_id: str) -> CloudFile:
        """Get file information from Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.api_base}/files/{file_id}?fields=id,name,size,mimeType,webViewLink,thumbnailLink,modifiedTime,createdTime,parents",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return CloudFile(
                    file_id=data["id"],
                    name=data["name"],
                    size=int(data.get("size", 0)),
                    mime_type=data["mimeType"],
                    provider="google_drive",
                    download_url=None,
                    web_view_url=data.get("webViewLink"),
                    thumbnail_url=data.get("thumbnailLink"),
                    modified_time=datetime.fromisoformat(data["modifiedTime"].replace("Z", "+00:00")),
                    created_time=datetime.fromisoformat(data["createdTime"].replace("Z", "+00:00")),
                    parent_folder_id=data.get("parents", [None])[0],
                    is_folder=data["mimeType"] == "application/vnd.google-apps.folder",
                    metadata=data
                )
            else:
                raise Exception(f"Failed to get file info: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error getting Google Drive file info: {str(e)}")
            raise
    
    def create_folder(self, name: str, parent_folder_id: str = None) -> CloudFolder:
        """Create folder in Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            if parent_folder_id:
                metadata["parents"] = [parent_folder_id]
            
            response = requests.post(
                f"{self.api_base}/files?fields=id,name,webViewLink,createdTime,modifiedTime",
                headers=headers,
                json=metadata
            )
            
            if response.status_code == 200:
                data = response.json()
                return CloudFolder(
                    folder_id=data["id"],
                    name=data["name"],
                    provider="google_drive",
                    parent_folder_id=parent_folder_id,
                    web_view_url=data.get("webViewLink"),
                    created_time=datetime.fromisoformat(data["createdTime"].replace("Z", "+00:00")),
                    modified_time=datetime.fromisoformat(data["modifiedTime"].replace("Z", "+00:00")),
                    file_count=0,
                    metadata=data
                )
            else:
                raise Exception(f"Failed to create folder: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error creating Google Drive folder: {str(e)}")
            raise
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file from Google Drive."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.delete(f"{self.api_base}/files/{file_id}", headers=headers)
            
            return response.status_code == 204
            
        except Exception as e:
            self.logger.error(f"Error deleting Google Drive file: {str(e)}")
            return False

class DropboxProvider(CloudStorageProvider):
    """Dropbox integration provider."""
    
    def __init__(self):
        self.access_token = None
        self.api_base = "https://api.dropboxapi.com/2"
        self.content_base = "https://content.dropboxapi.com/2"
        self.logger = logging.getLogger(__name__)
    
    def authenticate(self, access_token: str) -> bool:
        """Authenticate with Dropbox."""
        self.access_token = access_token
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.post(f"{self.api_base}/users/get_current_account", headers=headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Dropbox authentication failed: {str(e)}")
            return False
    
    def list_files(self, folder_id: str = None, file_type: str = None) -> List[CloudFile]:
        """List files in Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "path": folder_id or "",
                "recursive": False,
                "include_media_info": True
            }
            
            response = requests.post(f"{self.api_base}/files/list_folder", headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                files = []
                
                for item in result.get("entries", []):
                    if item[".tag"] == "file":
                        # Filter by file type if specified
                        if file_type and file_type == "pdf" and not item["name"].lower().endswith(".pdf"):
                            continue
                        
                        cloud_file = CloudFile(
                            file_id=item["id"],
                            name=item["name"],
                            size=item["size"],
                            mime_type=self._get_mime_type(item["name"]),
                            provider="dropbox",
                            download_url=None,
                            web_view_url=None,
                            thumbnail_url=None,
                            modified_time=datetime.fromisoformat(item["client_modified"].replace("Z", "+00:00")),
                            created_time=datetime.fromisoformat(item["client_modified"].replace("Z", "+00:00")),
                            parent_folder_id=folder_id,
                            is_folder=False,
                            metadata=item
                        )
                        files.append(cloud_file)
                
                return files
            else:
                self.logger.error(f"Failed to list Dropbox files: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing Dropbox files: {str(e)}")
            return []
    
    def upload_file(self, file_path: str, folder_id: str = None, name: str = None) -> CloudFile:
        """Upload file to Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            file_name = name or os.path.basename(file_path)
            dropbox_path = f"{folder_id or ''}/{file_name}".replace("//", "/")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Dropbox-API-Arg": json.dumps({
                    "path": dropbox_path,
                    "mode": "add",
                    "autorename": True
                }),
                "Content-Type": "application/octet-stream"
            }
            
            with open(file_path, 'rb') as file:
                response = requests.post(f"{self.content_base}/files/upload", headers=headers, data=file)
            
            if response.status_code == 200:
                data = response.json()
                return CloudFile(
                    file_id=data["id"],
                    name=data["name"],
                    size=data["size"],
                    mime_type=self._get_mime_type(data["name"]),
                    provider="dropbox",
                    download_url=None,
                    web_view_url=None,
                    thumbnail_url=None,
                    modified_time=datetime.fromisoformat(data["client_modified"].replace("Z", "+00:00")),
                    created_time=datetime.fromisoformat(data["client_modified"].replace("Z", "+00:00")),
                    parent_folder_id=folder_id,
                    is_folder=False,
                    metadata=data
                )
            else:
                raise Exception(f"Upload failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error uploading to Dropbox: {str(e)}")
            raise
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download file from Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Dropbox-API-Arg": json.dumps({"path": file_id})
            }
            
            response = requests.post(f"{self.content_base}/files/download", headers=headers)
            
            if response.status_code == 200:
                with open(local_path, 'wb') as file:
                    file.write(response.content)
                return True
            else:
                self.logger.error(f"Failed to download file: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading from Dropbox: {str(e)}")
            return False
    
    def get_file_info(self, file_id: str) -> CloudFile:
        """Get file information from Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"path": file_id}
            response = requests.post(f"{self.api_base}/files/get_metadata", headers=headers, json=data)
            
            if response.status_code == 200:
                item = response.json()
                return CloudFile(
                    file_id=item["id"],
                    name=item["name"],
                    size=item["size"],
                    mime_type=self._get_mime_type(item["name"]),
                    provider="dropbox",
                    download_url=None,
                    web_view_url=None,
                    thumbnail_url=None,
                    modified_time=datetime.fromisoformat(item["client_modified"].replace("Z", "+00:00")),
                    created_time=datetime.fromisoformat(item["client_modified"].replace("Z", "+00:00")),
                    parent_folder_id=None,
                    is_folder=False,
                    metadata=item
                )
            else:
                raise Exception(f"Failed to get file info: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error getting Dropbox file info: {str(e)}")
            raise
    
    def create_folder(self, name: str, parent_folder_id: str = None) -> CloudFolder:
        """Create folder in Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            folder_path = f"{parent_folder_id or ''}/{name}".replace("//", "/")
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"path": folder_path}
            response = requests.post(f"{self.api_base}/files/create_folder_v2", headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                metadata = result["metadata"]
                
                return CloudFolder(
                    folder_id=metadata["id"],
                    name=metadata["name"],
                    provider="dropbox",
                    parent_folder_id=parent_folder_id,
                    web_view_url=None,
                    created_time=datetime.utcnow(),
                    modified_time=datetime.utcnow(),
                    file_count=0,
                    metadata=metadata
                )
            else:
                raise Exception(f"Failed to create folder: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error creating Dropbox folder: {str(e)}")
            raise
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file from Dropbox."""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            data = {"path": file_id}
            response = requests.post(f"{self.api_base}/files/delete_v2", headers=headers, json=data)
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Error deleting Dropbox file: {str(e)}")
            return False
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        ext = filename.lower().split('.')[-1]
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        return mime_types.get(ext, 'application/octet-stream')

class CloudStorageManager:
    """Manages cloud storage integrations."""
    
    def __init__(self):
        self.providers = {
            "google_drive": GoogleDriveProvider(),
            "dropbox": DropboxProvider()
        }
        self.user_tokens: Dict[str, Dict[str, str]] = {}  # user_id -> provider -> token
        self.logger = logging.getLogger(__name__)
    
    def add_user_token(self, user_id: str, provider: str, access_token: str) -> bool:
        """Add user token for a cloud storage provider."""
        if provider not in self.providers:
            return False
        
        if user_id not in self.user_tokens:
            self.user_tokens[user_id] = {}
        
        # Authenticate with provider
        if self.providers[provider].authenticate(access_token):
            self.user_tokens[user_id][provider] = access_token
            self.logger.info(f"Added {provider} token for user {user_id}")
            return True
        else:
            self.logger.error(f"Failed to authenticate {provider} token for user {user_id}")
            return False
    
    def get_user_files(self, user_id: str, provider: str, folder_id: str = None, 
                      file_type: str = None) -> List[CloudFile]:
        """Get files for a user from a specific provider."""
        if not self._authenticate_user_provider(user_id, provider):
            return []
        
        return self.providers[provider].list_files(folder_id, file_type)
    
    def upload_to_cloud(self, user_id: str, provider: str, file_path: str, 
                       folder_id: str = None, name: str = None) -> Optional[CloudFile]:
        """Upload file to user's cloud storage."""
        if not self._authenticate_user_provider(user_id, provider):
            return None
        
        try:
            return self.providers[provider].upload_file(file_path, folder_id, name)
        except Exception as e:
            self.logger.error(f"Failed to upload to {provider}: {str(e)}")
            return None
    
    def download_from_cloud(self, user_id: str, provider: str, file_id: str, 
                           local_path: str) -> bool:
        """Download file from user's cloud storage."""
        if not self._authenticate_user_provider(user_id, provider):
            return False
        
        return self.providers[provider].download_file(file_id, local_path)
    
    def get_connected_providers(self, user_id: str) -> List[str]:
        """Get list of connected cloud storage providers for user."""
        if user_id not in self.user_tokens:
            return []
        
        return list(self.user_tokens[user_id].keys())
    
    def _authenticate_user_provider(self, user_id: str, provider: str) -> bool:
        """Authenticate user with provider."""
        if (user_id not in self.user_tokens or 
            provider not in self.user_tokens[user_id] or
            provider not in self.providers):
            return False
        
        token = self.user_tokens[user_id][provider]
        return self.providers[provider].authenticate(token)

# Global cloud storage manager instance
cloud_storage_manager = CloudStorageManager()