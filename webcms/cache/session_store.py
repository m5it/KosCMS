"""
Redis session storage backend.
"""

import json
import uuid
from typing import Optional, Dict


class RedisSessionStore:
    """Redis-backed session store."""

    def __init__(self, redis_client, ttl=86400):
        self.redis = redis_client
        self.ttl = ttl

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def create_session(self, data: Optional[Dict] = None) -> str:
        """Create new session."""
        session_id = str(uuid.uuid4())
        self.save_session(session_id, data or {})
        return session_id

    def save_session(self, session_id: str, data: Dict):
        """Save session data."""
        serialized = json.dumps(data, default=str)
        self.redis.get_client().setex(
            self._key(session_id),
            self.ttl,
            serialized
        )

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        data = self.redis.get_client().get(self._key(session_id))
        if data:
            return json.loads(data)
        return None

    def delete_session(self, session_id: str):
        """Delete session."""
        self.redis.get_client().delete(self._key(session_id))

    def update_session(self, session_id: str, data: Dict):
        """Update session data."""
        self.save_session(session_id, data)
