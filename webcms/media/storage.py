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
    """Local filesystem storage."""
    
    def __init__(self, base_path: str, base_url: str = "/media/"):
        self.base_path = Path(base_path)
        self.base_url = base_url
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file to local storage."""
        # Create folder structure
        if folder:
            target_dir = self.base_path / folder
        else:
            # Organize by date
            from datetime import datetime
            now = datetime.now()
            target_dir = self.base_path / str(now.year) / str(now.month)
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = target_dir / filename
        counter = 1
        while file_path.exists():
            name, ext = os.path.splitext(filename)
            file_path = target_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file_data, f)
        
        # Return relative path for URL
        return str(file_path.relative_to(self.base_path))
    
    def delete(self, path: str) -> bool:
        """Delete file."""
        full_path = self.base_path / path
        try:
            if full_path.exists():
                full_path.unlink()
                return True
        except Exception:
            pass
        return False
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return (self.base_path / path).exists()
    
    def get_url(self, path: str) -> str:
        """Get file URL."""
        return urljoin(self.base_url, path.replace("\\\\", "/"))


class S3Storage(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self, bucket: str, region: str = "us-east-1",
                 access_key: str = None, secret_key: str = None,
                 endpoint_url: str = None):
        self.bucket = bucket
        self.region = region
        
        # boto3 is optional
        try:
            import boto3
            self.s3 = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                endpoint_url=endpoint_url
            )
        except ImportError:
            self.s3 = None
    
    def save(self, file_data: BinaryIO, filename: str,
             folder: str = "") -> str:
        """Save file to S3."""
        if not self.s3:
            raise RuntimeError("boto3 not installed")
        
        key = f"{folder}/{filename}" if folder else filename
        
        self.s3.upload_fileobj(file_data, self.bucket, key)
        
        return key
    
    def delete(self, path: str) -> bool:
        """Delete file from S3."""
        if not self.s3:
            return False
        
        try:
            self.s3.delete_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False
    
    def exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        if not self.s3:
            return False
        
        try:
            self.s3.head_object(Bucket=self.bucket, Key=path)
            return True
        except Exception:
            return False
    
    def get_url(self, path: str) -> str:
        """Get S3 URL."""
        if self.region == "us-east-1":
            return f"https://{self.bucket}.s3.amazonaws.com/{path}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{path}"