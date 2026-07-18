"""
Real-time Features

Provides WebSocket support and real-time notifications
"""

import json
import asyncio
from typing import Dict, List, Set, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid


class RealtimeEvent(Enum):
    """Real-time event types."""
    CONTENT_UPDATED = 'content.updated'
    CONTENT_CREATED = 'content.created'
    CONTENT_DELETED = 'content.deleted'
    USER_ONLINE = 'user.online'
    USER_OFFLINE = 'user.offline'
    NOTIFICATION = 'notification'
    SYSTEM_MESSAGE = 'system.message'
    TYPING = 'typing'
    PRESENCE = 'presence'


@dataclass
class RealtimeMessage:
    """Real-time message."""
    event: str
    data: Dict
    timestamp: str
    sender: Optional[str] = None


class RealtimeManager:
    """Manages real-time connections and events."""
    
    def __init__(self):
        self.connections: Dict[str, Any] = {}  # user_id -> connection
        self.subscriptions: Dict[str, Set[str]] = {}  # event -> set of user_ids
        self.presence: Dict[str, Dict] = {}  # user_id -> presence info
        self.typing_indicators: Dict[str, Dict] = {}  # channel -> typing users
    
    def connect(self, user_id: str, connection: Any) -> bool:
        """
        Register a new connection.
        
        Args:
            user_id: User identifier
            connection: WebSocket connection object
        
        Returns:
            True if connected
        """
        self.connections[user_id] = connection
        self.presence[user_id] = {
            'online': True,
            'last_seen': self._now(),
            'status': 'online'
        }
        
        # Broadcast user online
        self.broadcast(RealtimeEvent.USER_ONLINE, {
            'user_id': user_id,
            'timestamp': self._now()
        })
        
        return True
    
    def disconnect(self, user_id: str) -> bool:
        """
        Unregister a connection.
        
        Args:
            user_id: User identifier
        
        Returns:
            True if disconnected
        """
        if user_id in self.connections:
            del self.connections[user_id]
        
        if user_id in self.presence:
            self.presence[user_id]['online'] = False
            self.presence[user_id]['last_seen'] = self._now()
        
        # Remove from all subscriptions
        for event, subscribers in self.subscriptions.items():
            subscribers.discard(user_id)
        
        # Broadcast user offline
        self.broadcast(RealtimeEvent.USER_OFFLINE, {
            'user_id': user_id,
            'timestamp': self._now()
        })
        
        return True
    
    def subscribe(self, user_id: str, event: str) -> bool:
        """
        Subscribe user to event.
        
        Args:
            user_id: User identifier
            event: Event type to subscribe to
        
        Returns:
            True if subscribed
        """
        if event not in self.subscriptions:
            self.subscriptions[event] = set()
        
        self.subscriptions[event].add(user_id)
        return True
    
    def unsubscribe(self, user_id: str, event: str) -> bool:
        """
        Unsubscribe user from event.
        
        Args:
            user_id: User identifier
            event: Event type to unsubscribe from
        
        Returns:
            True if unsubscribed
        """
        if event in self.subscriptions:
            self.subscriptions[event].discard(user_id)
        return True
    
    def send_to_user(self, user_id: str, event: RealtimeEvent, data: Dict) -> bool:
        """
        Send message to specific user.
        
        Args:
            user_id: Target user
            event: Event type
            data: Message data
        
        Returns:
            True if sent
        """
        if user_id not in self.connections:
            return False
        
        message = RealtimeMessage(
            event=event.value,
            data=data,
            timestamp=self._now()
        )
        
        try:
            # Send via WebSocket
            connection = self.connections[user_id]
            if hasattr(connection, 'send'):
                connection.send(json.dumps({
                    'event': message.event,
                    'data': message.data,
                    'timestamp': message.timestamp
                }))
            return True
        except Exception:
            return False
    
    def broadcast(self, event: RealtimeEvent, data: Dict, 
                  exclude: Optional[List[str]] = None) -> int:
        """
        Broadcast event to all subscribers.
        
        Args:
            event: Event type
            data: Message data
            exclude: User IDs to exclude
        
        Returns:
            Number of recipients
        """
        exclude = exclude or []
        event_str = event.value
        
        # Get subscribers
        subscribers = self.subscriptions.get(event_str, set()).copy()
        
        # Add all users for system events
        if event in [RealtimeEvent.SYSTEM_MESSAGE, RealtimeEvent.NOTIFICATION]:
            subscribers.update(self.connections.keys())
        
        sent = 0
        for user_id in subscribers:
            if user_id not in exclude:
                if self.send_to_user(user_id, event, data):
                    sent += 1
        
        return sent
    
    def notify_content_change(self, content_id: str, content_type: str,
                             action: str, user_id: str, 
                             data: Optional[Dict] = None):
        """
        Notify about content changes.
        
        Args:
            content_id: Content identifier
            content_type: Type of content (page, post, etc.)
            action: Action performed (created, updated, deleted)
            user_id: User who made the change
            data: Additional data
        """
        event_map = {
            'created': RealtimeEvent.CONTENT_CREATED,
            'updated': RealtimeEvent.CONTENT_UPDATED,
            'deleted': RealtimeEvent.CONTENT_DELETED
        }
        
        event = event_map.get(action, RealtimeEvent.CONTENT_UPDATED)
        
        self.broadcast(event, {
            'content_id': content_id,
            'content_type': content_type,
            'action': action,
            'user_id': user_id,
            'data': data or {},
            'timestamp': self._now()
        }, exclude=[user_id])  # Don't notify the person who made the change
    
    def send_notification(self, user_id: str, notification_type: str,
                         title: str, message: str, 
                         data: Optional[Dict] = None) -> bool:
        """
        Send notification to user.
        
        Args:
            user_id: Target user
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional data
        
        Returns:
            True if sent
        """
        return self.send_to_user(user_id, RealtimeEvent.NOTIFICATION, {
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data or {},
            'timestamp': self._now()
        })
    
    def set_typing(self, user_id: str, channel: str, 
                   is_typing: bool = True) -> bool:
        """
        Set typing indicator.
        
        Args:
            user_id: User typing
            channel: Channel/resource being typed in
            is_typing: Whether user is typing
        
        Returns:
            True if set
        """
        if channel not in self.typing_indicators:
            self.typing_indicators[channel] = {}
        
        if is_typing:
            self.typing_indicators[channel][user_id] = {
                'since': self._now(),
                'user_id': user_id
            }
        else:
            if user_id in self.typing_indicators[channel]:
                del self.typing_indicators[channel][user_id]
        
        # Broadcast typing status
        self.broadcast(RealtimeEvent.TYPING, {
            'channel': channel,
            'users': list(self.typing_indicators.get(channel, {}).keys()),
            'timestamp': self._now()
        })
        
        return True
    
    def get_online_users(self) -> List[Dict]:
        """
        Get list of online users.
        
        Returns:
            List of online users with presence info
        """
        online = []
        for user_id, info in self.presence.items():
            if info.get('online'):
                online.append({
                    'user_id': user_id,
                    'status': info.get('status', 'online'),
                    'last_seen': info.get('last_seen')
                })
        return online
    
    def update_presence(self, user_id: str, status: str):
        """
        Update user presence status.
        
        Args:
            user_id: User identifier
            status: New status (online, away, busy, etc.)
        """
        if user_id in self.presence:
            self.presence[user_id]['status'] = status
            self.presence[user_id]['last_seen'] = self._now()
        
        self.broadcast(RealtimeEvent.PRESENCE, {
            'user_id': user_id,
            'status': status,
            'timestamp': self._now()
        })
    
    def _now(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()


class CollaborationManager:
    """Manages real-time collaboration features."""
    
    def __init__(self, realtime_manager: RealtimeManager):
        self.rtm = realtime_manager
        self.active_edits: Dict[str, Dict] = {}  # content_id -> edit info
        self.locks: Dict[str, str] = {}  # content_id -> user_id
    
    def start_editing(self, content_id: str, user_id: str, 
                      user_name: str) -> bool:
        """
        Start editing a document.
        
        Args:
            content_id: Content being edited
            user_id: User editing
            user_name: User display name
        
        Returns:
            True if editing started
        """
        if content_id in self.active_edits:
            return False  # Someone else is editing
        
        self.active_edits[content_id] = {
            'user_id': user_id,
            'user_name': user_name,
            'started_at': self.rtm._now(),
            'content_id': content_id
        }
        
        # Notify others
        self.rtm.broadcast(RealtimeEvent.SYSTEM_MESSAGE, {
            'type': 'edit_started',
            'content_id': content_id,
            'user_id': user_id,
            'user_name': user_name
        }, exclude=[user_id])
        
        return True
    
    def stop_editing(self, content_id: str, user_id: str) -> bool:
        """
        Stop editing a document.
        
        Args:
            content_id: Content being edited
            user_id: User stopping
        
        Returns:
            True if stopped
        """
        if content_id not in self.active_edits:
            return False
        
        edit_info = self.active_edits[content_id]
        if edit_info['user_id'] != user_id:
            return False  # Not the editor
        
        del self.active_edits[content_id]
        
        # Notify others
        self.rtm.broadcast(RealtimeEvent.SYSTEM_MESSAGE, {
            'type': 'edit_ended',
            'content_id': content_id,
            'user_id': user_id
        }, exclude=[user_id])
        
        return True
    
    def is_being_edited(self, content_id: str) -> Optional[Dict]:
        """
        Check if content is being edited.
        
        Args:
            content_id: Content to check
        
        Returns:
            Edit info or None
        """
        return self.active_edits.get(content_id)
    
    def acquire_lock(self, content_id: str, user_id: str) -> bool:
        """
        Acquire exclusive lock on content.
        
        Args:
            content_id: Content to lock
            user_id: User requesting lock
        
        Returns:
            True if lock acquired
        """
        if content_id in self.locks:
            return self.locks[content_id] == user_id
        
        self.locks[content_id] = user_id
        return True
    
    def release_lock(self, content_id: str, user_id: str) -> bool:
        """
        Release lock on content.
        
        Args:
            content_id: Content to unlock
            user_id: User releasing lock
        
        Returns:
            True if lock released
        """
        if content_id in self.locks and self.locks[content_id] == user_id:
            del self.locks[content_id]
            return True
        return False


# Global instances
realtime_manager = RealtimeManager()
collaboration_manager = CollaborationManager(realtime_manager)


# Export
__all__ = [
    'RealtimeEvent',
    'RealtimeMessage',
    'RealtimeManager',
    'CollaborationManager',
    'realtime_manager',
    'collaboration_manager'
]
