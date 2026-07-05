"""
Session Management with Redis

Server-side session storage with expiration.
"""

import json
import secrets
from typing import Dict, Optional, Any
from datetime import datetime, timedelta


class SessionManager:
    """Redis-backed session management."""
    
    def __init__(self, redis_client=None, session_timeout: int = 3600):
        self.redis = redis_client
        self.session_timeout = session_timeout
        self.prefix = "session:"
        
        # Fallback to memory if no Redis
        if redis_client is None:
            self._memory: Dict[str, Dict] = {}
    
    def create_session(self, user_id: str, 
                       extra_data: Optional[Dict] = None) -> str:
        """
        Create new session.
        
        Args:
            user_id: User identifier
            extra_data: Additional session data
        
        Returns:
            Session ID
        """
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_access": datetime.utcnow().isoformat(),
            "data": extra_data or {}
        }
        
        if self.redis:
            key = f"{self.prefix}{session_id}"
            self.redis.setex(
                key,
                self.session_timeout,
                json.dumps(session_data)
            )
        else:
            self._memory[session_id] = session_data
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session data.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data or None
        """
        if self.redis:
            key = f"{self.prefix}{session_id}"
            data = self.redis.get(key)
            if data:
                session_data = json.loads(data)
                # Update last access
                session_data["last_access"] = datetime.utcnow().isoformat()
                self.redis.setex(key, self.session_timeout, 
                                json.dumps(session_data))
                return session_data
            return None
        else:
            return self._memory.get(session_id)
    
    def update_session(self, session_id: str, 
                       data: Dict) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            data: New session data
        
        Returns:
            True if updated
        """
        session = self.get_session(session_id)
        if session is None:
            return False
        
        session["data"].update(data)
        session["last_access"] = datetime.utcnow().isoformat()
        
        if self.redis:
            key = f"{self.prefix}{session_id}"
            self.redis.setex(
                key,
                self.session_timeout,
                json.dumps(session)
            )
        else:
            self._memory[session_id] = session
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted
        """
        if self.redis:
            key = f"{self.prefix}{session_id}"
            return self.redis.delete(key) > 0
        else:
            return self._memory.pop(session_id, None) is not None
    
    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all sessions for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of session IDs
        """
        sessions = []
        
        if self.redis:
            # Scan for user sessions
            pattern = f"{self.prefix}*"
            for key in self.redis.scan_iter(pattern):
                data = self.redis.get(key)
                if data:
                    session = json.loads(data)
                    if session.get("user_id") == user_id:
                        sessions.append(key.decode().replace(self.prefix, ""))
        else:
            for sid, session in self._memory.items():
                if session.get("user_id") == user_id:
                    sessions.append(sid)
        
        return sessions
    
    def invalidate_user_sessions(self, user_id: str) -> int:
        """
        Delete all sessions for user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of sessions deleted
        """
        sessions = self.get_user_sessions(user_id)
        count = 0
        
        for session_id in sessions:
            if self.delete_session(session_id):
                count += 1
        
        return count