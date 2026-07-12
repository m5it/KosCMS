"""
Version model for content history tracking.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional


class Version:
    """
    Represents a snapshot of content at a specific point in time.
    """
    
    def __init__(
        self,
        content_id: str,
        content_type: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        version_number: Optional[int] = None,
        comment: Optional[str] = None,
        version_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.version_id = version_id or str(uuid.uuid4())
        self.content_id = content_id
        self.content_type = content_type  # 'post', 'page', etc.
        self.data = data
        self.user_id = user_id
        self.username = username
        self.version_number = version_number or 1
        self.comment = comment or ""
        self.created_at = created_at or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "version_id": self.version_id,
            "content_id": self.content_id,
            "content_type": self.content_type,
            "version_number": self.version_number,
            "data": self.data,
            "user_id": self.user_id,
            "username": self.username,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Version":
        """Create version from dictionary."""
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            content_id=data["content_id"],
            content_type=data["content_type"],
            data=data.get("data", {}),
            user_id=data.get("user_id"),
            username=data.get("username"),
            version_number=data.get("version_number", 1),
            comment=data.get("comment", ""),
            version_id=data.get("version_id"),
            created_at=created_at
        )
    
    def __repr__(self) -> str:
        return f"<Version {self.content_type}:{self.content_id} v{self.version_number}>"
