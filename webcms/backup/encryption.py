"""
Backup encryption helpers.
"""

from cryptography.fernet import Fernet


class BackupEncryption:
    """Encrypt and decrypt backup data."""

    def __init__(self, key: bytes = None):
        self.key = key or Fernet.generate_key()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> bytes:
        """Encrypt string data."""
        return self.fernet.encrypt(data.encode())

    def decrypt(self, token: bytes) -> str:
        """Decrypt data."""
        return self.fernet.decrypt(token).decode()

    def get_key(self) -> bytes:
        """Get encryption key."""
        return self.key
