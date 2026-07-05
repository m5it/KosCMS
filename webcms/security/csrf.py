"""
CSRF Protection

Token generation and validation.
"""

import secrets
import hmac
import hashlib
from typing import Optional


class CSRFProtection:
    """CSRF token protection."""
    
    def __init__(self, secret_key: str, token_length: int = 32):
        self.secret_key = secret_key.encode()
        self.token_length = token_length
    
    def generate_token(self, session_id: str = None) -> str:
        """
        Generate CSRF token.
        
        Args:
            session_id: Optional session identifier
        
        Returns:
            CSRF token string
        """
        # Create token with session binding
        token = secrets.token_hex(self.token_length)
        
        if session_id:
            # Bind to session
            signature = hmac.new(
                self.secret_key,
                f"{token}:{session_id}".encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            return f"{token}:{signature}"
        
        return token
    
    def validate_token(self, token: str, session_id: str = None) -> bool:
        """
        Validate CSRF token.
        
        Args:
            token: Token to validate
            session_id: Session identifier
        
        Returns:
            True if valid
        """
        if not token:
            return False
        
        if session_id and ":" in token:
            # Check signature
            parts = token.rsplit(":", 1)
            if len(parts) != 2:
                return False
            
            token_part, signature = parts
            expected = hmac.new(
                self.secret_key,
                f"{token_part}:{session_id}".encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            return hmac.compare_digest(signature, expected)
        
        # Simple token validation - check format
        return len(token) == self.token_length * 2
    
    def get_token_from_request(self, request) -> Optional[str]:
        """
        Extract CSRF token from request.
        
        Checks header first, then form data.
        
        Args:
            request: Request object
        
        Returns:
            Token or None
        """
        # Check header
        token = request.get_header("X-CSRF-Token")
        if token:
            return token
        
        # Check form data
        if request.form:
            return request.form.get("_csrf_token")
        
        return None