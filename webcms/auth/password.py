"""
Password Hashing with bcrypt

Secure password storage with salt and configurable rounds.
"""

import bcrypt
import secrets
import re
from typing import Tuple


class PasswordHasher:
    """Secure password hashing using bcrypt."""
    
    def __init__(self, rounds: int = 12):
        self.rounds = rounds
    
    def hash_password(self, password: str) -> str:
        """
        Hash password with random salt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password string
        """
        # Validate password strength
        self._validate_password(password)
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        
        return hashed.decode("utf-8")
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed: Stored hash
        
        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashed.encode("utf-8")
            )
        except Exception:
            return False
    
    def _validate_password(self, password: str) -> None:
        """
        Validate password strength.
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain uppercase letter")
        
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain lowercase letter")
        
        if not re.search(r"\d", password):
            raise ValueError("Password must contain digit")
        
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain special character")
    
    def generate_reset_token(self) -> str:
        """Generate secure password reset token."""
        return secrets.token_urlsafe(32)
    
    def needs_rehash(self, hashed: str) -> bool:
        """
        Check if password needs rehashing (rounds changed).
        
        Args:
            hashed: Stored hash
        
        Returns:
            True if should rehash
        """
        # Extract rounds from hash
        try:
            # bcrypt hash format: $2b$rounds$salt+hash
            parts = hashed.split("$")
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < self.rounds
        except (ValueError, IndexError):
            pass
        return True