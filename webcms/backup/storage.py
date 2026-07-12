"""
Backup storage backends: S3, Azure, Local.
"""

import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional


class StorageBackend(ABC):
    """Base storage backend."""

    @abstractmethod
    async def store(self, key: str, data: str):
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def store_file(self, file_path: str) -> str:
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage."""

    def __init__(self, base_path="backups"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def store(self, key: str, data: str):
        path = os.path.join(self.base_path, key)
        with open(path, "w") as f:
            f.write(data)
        return path

    async def retrieve(self, key: str) -> Optional[str]:
        path = os.path.join(self.base_path, key)
        if not os.path.exists(path):
            return None
        with open(path, "r") as f:
            return f.read()

    async def store_file(self, file_path: str) -> str:
        """Copy file to backup location."""
        filename = os.path.basename(file_path)
        dest = os.path.join(self.base_path, filename)
        shutil.copy2(file_path, dest)
        return dest


class S3Storage(StorageBackend):
    """AWS S3 storage backend."""

    def __init__(self, bucket, access_key=None, secret_key=None, region="us-east-1"):
        self.bucket = bucket
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region

    async def store(self, key: str, data: str):
        # Placeholder: boto3 upload
        return f"s3://{self.bucket}/{key}"

    async def retrieve(self, key: str) -> Optional[str]:
        return f"s3://{self.bucket}/{key}"

    async def store_file(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        return f"s3://{self.bucket}/{filename}"


class AzureStorage(StorageBackend):
    """Azure Blob storage backend."""

    def __init__(self, container, connection_string=None):
        self.container = container
        self.connection_string = connection_string

    async def store(self, key: str, data: str):
        return f"azure://{self.container}/{key}"

    async def retrieve(self, key: str) -> Optional[str]:
        return f"azure://{self.container}/{key}"

    async def store_file(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        return f"azure://{self.container}/{filename}"
