#!/usr/bin/env python3
"""Unit tests for backup encryption."""

from webcms.backup.encryption import BackupEncryption


def test_encrypt_decrypt():
    encryption = BackupEncryption()
    original = "sensitive data"
    encrypted = encryption.encrypt(original)
    decrypted = encryption.decrypt(encrypted)
    assert decrypted == original


def test_key_generation():
    encryption = BackupEncryption()
    assert len(encryption.get_key()) > 0
