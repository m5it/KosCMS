"""
JWT Token Handler

Access and refresh token management with expiration.
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class JWTHandler:
    """JWT token creation and validation."""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=15)
        self.refresh_token_expire = timedelta(days=7)
    
    def create_tokens(self, user_id: str, extra_claims: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Create access and refresh tokens.
        
        Returns:
            Tuple of (access_token, refresh_token)
        """
        now = datetime.utcnow()
        
        # Access token
        access_payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.access_token_expire,
            "type": "access",
            "jti": secrets.token_hex(16)
        }
        if extra_claims:
            access_payload.update(extra_claims)
        
        access_token = jwt.encode(
            access_payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        # Refresh token
        refresh_payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "type": "refresh",
            "jti": secrets.token_hex(16)
        }
        
        refresh_token = jwt.encode(
            refresh_payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return access_token, refresh_token
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """
        Verify and decode token.
        
        Args:
            token: JWT token string
            token_type: Expected token type
        
        Returns:
            Token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token from refresh token.
        
        Returns:
            New access token or None if refresh token invalid
        """
        payload = self.verify_token(refresh_token, "refresh")
        if payload is None:
            return None
        
        # Create new access token
        user_id = payload["sub"]
        return self.create_tokens(user_id)[0]
    
    def revoke_token(self, token: str) -> bool:
        """
        Mark token as revoked (requires token blacklist).
        
        Returns:
            True if token was valid and is now revoked
        """
        payload = self.verify_token(token)
        if payload is None:
            return False
        
        # In production, add jti to Redis blacklist
        # For now, just return True
        return True