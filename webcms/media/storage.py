"""
Storage Backends

Local filesystem, S3, and Azure storage implementations.
Includes WebP support and Accept header detection.
"""

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, Dict
from urllib.parse import urljoin


class WebPSupport:
    """WebP support detection."""
    
    @staticmethod
    def supports_webp(accept_header: str) -> bool:
        """Check if browser supports WebP."""
        if not accept_header:
            return False
        return "image/webp" in accept_header
    
    @staticmethod
    def get_preferred_format(accept_header: str, 
                            available_formats: Dict[str, str]) -> str:
        """
        Get preferred image format based on Accept header.
        
        Args:
            accept_header: HTTP Accept header
            available_formats: Dict of mime_type -> url
        
        Returns:
            URL of preferred format
        """
        if "image/webp" in accept_header and "image/webp" in available_formats:
            return available_formats["image/webp"]
        
        # Fallback to JPEG or original
        for mime in ["image/jpeg", "image/png", "image/gif"]:
            if mime in available_formats:
                return available_formats[mime]
        
        # Return first available
        return next(iter(available_formats.values()))


class StorageBackend(ABC):
    """Abstract storage backend."""
    
    @abstractmethod
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file and return URL."""
        pass
    
    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete file."""
        pass
    
    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        pass
    
    @abstractmethod
    def get_url(self, path: str) -> str:
        """Get file URL."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage with WebP support."""
    
    def __init__(self, base_path: str = "uploads", 
                 base_url: str = "/uploads"):
        self.base_path = Path(base_path)
        self.base_url = base_url
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, filename: str, folder: str = "") -> Path:
        """Get full filesystem path."""
        if folder:
            path = self.base_path / folder / filename
        else:
            path = self.base_path / filename
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file and return URL."""
        full_path = self._get_full_path(filename, folder)
        
        with open(full_path, 'wb') as f:
            shutil.copyfileobj(file_data, f)
        
        return self.get_url(str(full_path.relative_to(self.base_path)))
    
    def delete(self, path: str) -> bool:
        """Delete file."""
        full_path = self.base_path / path
        if full_path.exists():
            full_path.unlink()
            return True
        return False
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / path).exists()
    
    def get_url(self, path: str) -> str:
        """Get file URL."""
        return urljoin(self.base_url, path.replace("\\", "/"))
    
    def get_webp_path(self, path: str) -> Optional[Path]:
        """Get WebP version path if exists."""
        base = self.base_path / path
        webp_path = base.with_suffix('.webp')
        if webp_path.exists():
            return webp_path
        return None


class S3Storage(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self, bucket: str, region: str = "us-east-1",
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None):
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self._client = None
    
    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    's3',
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )
            except ImportError:
                raise RuntimeError("boto3 required for S3 storage")
        return self._client
    
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file to S3."""
        key = f"{folder}/{filename}" if folder else filename
        self._get_client().upload_fileobj(file_data, self.bucket, key)
        return self.get_url(key)
    
    def delete(self, path: str) -> bool:
        """Delete from S3."""
        try:
            self._get_client().delete_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if exists in S3."""
        try:
            self._get_client().head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False
    
    def get_url(self, path: str) -> str:
        """Get S3 URL."""
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{path}"


class AzureStorage(StorageBackend):
    """Azure Blob storage backend."""
    
    def __init__(self, account_name: str, container: str,
                 account_key: Optional[str] = None):
        self.account_name = account_name
        self.container = container
        self.account_key = account_key
        self._client = None
    
    def _get_client(self):
        """Get or create Azure client."""
        if self._client is None:
            try:
                from azure.storage.blob import BlobServiceClient
                conn_str = f"DefaultEndpointsProtocol=https;AccountName={self.account_name};"
                if self.account_key:
                    conn_str += f"AccountKey={self.account_key};"
                conn_str += f"EndpointSuffix=core.windows.net"
                self._client = BlobServiceClient.from_connection_string(conn_str)
            except ImportError:
                raise RuntimeError("azure-storage-blob required for Azure storage")
        return self._client
    
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file to Azure."""
        blob_name = f"{folder}/{filename}" if folder else filename
        blob_client = self._get_client().get_blob_client(
            container=self.container, blob=blob_name
        )
        blob_client.upload_blob(file_data)
        return self.get_url(blob_name)
    
    def delete(self, path: str) -> bool:
        """Delete from Azure."""
        try:
            blob_client = self._get_client().get_blob_client(
                container=self.container, blob=path
            )
            blob_client.delete_blob()
            return True
        except Exception:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if exists in Azure."""
        try:
            blob_client = self._get_client().get_blob_client(
                container=self.container, blob=path
            )
            blob_client.get_blob_properties()
            return True
        except Exception:
            return False
    
    def get_url(self, path: str) -> str:
        """Get Azure URL."""
        return f"https://{self.account_name}.blob.core.windows.net/{self.container}/{path}"
