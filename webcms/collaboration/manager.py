"""
Collaboration Manager for WebCMS

Manages user sessions, presence, and document locks.
"""

import time
from typing import Dict, List, Optional


class UserPresence:
    """User presence information."""
    def __init__(self, user_id, username, document_id, color="#000000"):
        self.user_id = user_id
        self.username = username
        self.document_id = document_id
        self.cursor_position = 0
        self.selection_start = 0
        self.selection_end = 0
        self.last_activity = time.time()
        self.is_typing = False
        self.color = color
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "cursor_position": self.cursor_position,
            "selection": [self.selection_start, self.selection_end],
            "is_typing": self.is_typing,
            "color": self.color
        }


class DocumentLock:
    """Lock on a document section."""
    def __init__(self, user_id, document_id, start, end):
        self.user_id = user_id
        self.document_id = document_id
        self.start = start
        self.end = end
        self.acquired_at = time.time()
    
    def is_expired(self, timeout=300):
        """Check if lock has expired (default 5 minutes)."""
        return time.time() - self.acquired_at > timeout


class CollaborationManager:
    """Manages collaborative editing sessions."""
    
    def __init__(self):
        self.presence: Dict[str, Dict[str, UserPresence]] = {}
        self.locks: Dict[str, List[DocumentLock]] = {}
        self.connections: Dict[str, Dict[str, object]] = {}
        
        self.user_colors = [
            "#E91E63", "#9C27B0", "#673AB7", "#3F51B5",
            "#2196F3", "#03A9F4", "#00BCD4", "#009688",
            "#4CAF50", "#8BC34A", "#CDDC39", "#FFEB3B",
            "#FFC107", "#FF9800", "#FF5722", "#795548"
        ]
        self._color_index = 0
    
    def _get_user_color(self):
        color = self.user_colors[self._color_index % len(self.user_colors)]
        self._color_index += 1
        return color
    
    async def join_document(self, user_id, username, document_id):
        if document_id not in self.presence:
            self.presence[document_id] = {}
            self.connections[document_id] = {}
        
        presence = UserPresence(user_id, username, document_id, self._get_user_color())
        self.presence[document_id][user_id] = presence
        return presence
    
    async def leave_document(self, user_id, document_id):
        if document_id in self.presence:
            self.presence[document_id].pop(user_id, None)
            self.connections[document_id].pop(user_id, None)
            if not self.presence[document_id]:
                del self.presence[document_id]
                del self.connections[document_id]
    
    async def update_presence(self, user_id, document_id, cursor_position=None,
                            selection_start=None, selection_end=None, is_typing=None):
        if document_id not in self.presence:
            return
        
        presence = self.presence[document_id].get(user_id)
        if not presence:
            return
        
        if cursor_position is not None:
            presence.cursor_position = cursor_position
        if selection_start is not None:
            presence.selection_start = selection_start
        if selection_end is not None:
            presence.selection_end = selection_end
        if is_typing is not None:
            presence.is_typing = is_typing
        
        presence.last_activity = time.time()
    
    async def acquire_lock(self, user_id, document_id, start, end):
        """Try to acquire a lock on a document section."""
        self._clean_expired_locks(document_id)
        
        for lock in self.locks.get(document_id, []):
            if lock.user_id != user_id:
                if not (end <= lock.start or start >= lock.end):
                    return False
        
        if document_id not in self.locks:
            self.locks[document_id] = []
        
        lock = DocumentLock(user_id, document_id, start, end)
        self.locks[document_id].append(lock)
        return True
    
    async def release_lock(self, user_id, document_id, start, end):
        """Release a lock on a document section."""
        if document_id not in self.locks:
            return
        
        self.locks[document_id] = [
            lock for lock in self.locks[document_id]
            if not (lock.user_id == user_id and lock.start == start and lock.end == end)
        ]
    
    async def release_user_locks(self, user_id, document_id):
        """Release all locks held by a user."""
        if document_id not in self.locks:
            return
        
        self.locks[document_id] = [
            lock for lock in self.locks[document_id]
            if lock.user_id != user_id
        ]
    
    def _clean_expired_locks(self, document_id):
        """Remove expired locks."""
        if document_id not in self.locks:
            return
        
        self.locks[document_id] = [
            lock for lock in self.locks[document_id]
            if not lock.is_expired()
        ]
    
    def get_active_users(self, document_id):
        if document_id not in self.presence:
            return []
        return [p.to_dict() for p in self.presence[document_id].values()]
    
    def is_section_locked(self, document_id, start, end):
        """Check if a section is locked by another user."""
        for lock in self.locks.get(document_id, []):
            if not (end <= lock.start or start >= lock.end):
                return lock.user_id
        return None
    
    def register_connection(self, user_id, document_id, websocket):
        if document_id not in self.connections:
            self.connections[document_id] = {}
        self.connections[document_id][user_id] = websocket
