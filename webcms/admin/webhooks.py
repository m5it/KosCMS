"""
Webhook System for Admin Panel

Provides event-driven webhooks for integrations with external systems
"""

import json
import hmac
import hashlib
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class WebhookEvent(Enum):
    """Webhook event types."""
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    
    CONTENT_CREATED = 'content.created'
    CONTENT_UPDATED = 'content.updated'
    CONTENT_DELETED = 'content.deleted'
    CONTENT_PUBLISHED = 'content.published'
    
    MEDIA_UPLOADED = 'media.uploaded'
    MEDIA_DELETED = 'media.deleted'
    
    SETTINGS_CHANGED = 'settings.changed'
    
    BACKUP_CREATED = 'backup.created'
    BACKUP_RESTORED = 'backup.restored'


@dataclass
class Webhook:
    """Webhook configuration."""
    id: str
    url: str
    events: List[str]
    secret: Optional[str]
    active: bool
    created_at: str
    last_triggered: Optional[str] = None
    failure_count: int = 0


class WebhookManager:
    """Manage webhooks and trigger events."""
    
    def __init__(self, db=None):
        self.db = db
        self._ensure_table()
        self._webhooks_cache = {}
        self._load_webhooks()
    
    def _ensure_table(self):
        """Ensure webhooks table exists."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'webhooks' not in tables:
                self.db.execute("""
                    CREATE TABLE webhooks (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        events TEXT NOT NULL,
                        secret TEXT,
                        active INTEGER DEFAULT 1,
                        created_at TEXT,
                        last_triggered TEXT,
                        failure_count INTEGER DEFAULT 0
                    )
                """)
        except Exception:
            pass
    
    def _load_webhooks(self):
        """Load webhooks from database."""
        if not self.db:
            return
        
        try:
            result = self.db.query("SELECT * FROM webhooks WHERE active = 1")
            for row in result.get('rows', []):
                webhook = Webhook(
                    id=row['id'],
                    url=row['url'],
                    events=json.loads(row['events']),
                    secret=row.get('secret'),
                    active=bool(row['active']),
                    created_at=row['created_at'],
                    last_triggered=row.get('last_triggered'),
                    failure_count=row.get('failure_count', 0)
                )
                self._webhooks_cache[row['id']] = webhook
        except Exception:
            pass
    
    def create_webhook(self, url: str, events: List[str], secret: Optional[str] = None) -> Webhook:
        """
        Create a new webhook.
        
        Args:
            url: Webhook endpoint URL
            events: List of events to subscribe to
            secret: Optional secret for HMAC signature
        
        Returns:
            Created webhook
        """
        webhook_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        webhook = Webhook(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret,
            active=True,
            created_at=created_at
        )
        
        # Save to database
        if self.db:
            try:
                self.db.execute(f"""
                    INSERT INTO webhooks (id, url, events, secret, active, created_at, failure_count)
                    VALUES (
                        '{webhook_id}',
                        '{url}',
                        '{json.dumps(events)}',
                        '{secret or ''}',
                        1,
                        '{created_at}',
                        0
                    )
                """)
            except Exception:
                pass
        
        # Add to cache
        self._webhooks_cache[webhook_id] = webhook
        
        return webhook
    
    def update_webhook(self, webhook_id: str, **kwargs) -> Optional[Webhook]:
        """Update webhook configuration."""
        if webhook_id not in self._webhooks_cache:
            return None
        
        webhook = self._webhooks_cache[webhook_id]
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(webhook, key):
                setattr(webhook, key, value)
        
        # Update database
        if self.db:
            try:
                updates = []
                for key, value in kwargs.items():
                    if key == 'events':
                        value = json.dumps(value)
                    updates.append(f"{key} = '{value}'")
                
                if updates:
                    self.db.execute(f"""
                        UPDATE webhooks 
                        SET {', '.join(updates)}
                        WHERE id = '{webhook_id}'
                    """)
            except Exception:
                pass
        
        return webhook
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if webhook_id not in self._webhooks_cache:
            return False
        
        del self._webhooks_cache[webhook_id]
        
        if self.db:
            try:
                self.db.execute(f"DELETE FROM webhooks WHERE id = '{webhook_id}'")
            except Exception:
                pass
        
        return True
    
    def list_webhooks(self) -> List[Webhook]:
        """List all webhooks."""
        return list(self._webhooks_cache.values())
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID."""
        return self._webhooks_cache.get(webhook_id)
    
    def trigger_event(self, event: WebhookEvent, payload: Dict):
        """
        Trigger a webhook event.
        
        Args:
            event: Event type
            payload: Event data
        """
        event_str = event.value if isinstance(event, WebhookEvent) else event
        
        # Find matching webhooks
        matching_webhooks = [
            wh for wh in self._webhooks_cache.values()
            if wh.active and (event_str in wh.events or '*' in wh.events)
        ]
        
        # Trigger asynchronously
        for webhook in matching_webhooks:
            threading.Thread(
                target=self._send_webhook,
                args=(webhook, event_str, payload),
                daemon=True
            ).start()
    
    def _send_webhook(self, webhook: Webhook, event: str, payload: Dict):
        """Send webhook request."""
        # Prepare payload
        delivery_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        full_payload = {
            'event': event,
            'timestamp': timestamp,
            'delivery_id': delivery_id,
            'data': payload
        }
        
        body = json.dumps(full_payload, default=str)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Event': event,
            'X-Webhook-Delivery': delivery_id,
            'X-Webhook-Timestamp': timestamp,
            'User-Agent': 'WebCMS-Webhook/1.0'
        }
        
        # Add signature if secret exists
        if webhook.secret:
            signature = self._sign_payload(body, webhook.secret)
            headers['X-Webhook-Signature'] = signature
        
        try:
            response = requests.post(
                webhook.url,
                data=body,
                headers=headers,
                timeout=30,
                verify=True
            )
            
            # Update last triggered
            webhook.last_triggered = timestamp
            
            # Reset failure count on success
            if response.status_code < 400:
                webhook.failure_count = 0
            else:
                webhook.failure_count += 1
            
            # Update database
            if self.db:
                self.db.execute(f"""
                    UPDATE webhooks 
                    SET last_triggered = '{timestamp}',
                        failure_count = {webhook.failure_count}
                    WHERE id = '{webhook.id}'
                """)
            
        except Exception as e:
            webhook.failure_count += 1
            
            if self.db:
                self.db.execute(f"""
                    UPDATE webhooks 
                    SET failure_count = {webhook.failure_count}
                    WHERE id = '{webhook.id}'
                """)
    
    def _sign_payload(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return f'sha256={signature}'
    
    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature."""
        expected = self._sign_payload(payload, secret)
        return hmac.compare_digest(expected, signature)


class EventEmitter:
    """Event emitter for internal use."""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable):
        """Register event handler."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable):
        """Unregister event handler."""
        if event in self._handlers:
            self._handlers[event].remove(handler)
    
    def emit(self, event: str, **kwargs):
        """Emit event to all handlers."""
        if event in self._handlers:
            for handler in self._handlers[event]:
                try:
                    handler(**kwargs)
                except Exception:
                    pass
    
    def emit_async(self, event: str, **kwargs):
        """Emit event asynchronously."""
        threading.Thread(
            target=self.emit,
            args=(event,),
            kwargs=kwargs,
            daemon=True
        ).start()


# Global instances
webhook_manager = WebhookManager()
event_emitter = EventEmitter()


def emit_event(event: WebhookEvent, **kwargs):
    """Emit event to webhooks and internal handlers."""
    # Emit to internal handlers
    event_emitter.emit(event.value, **kwargs)
    
    # Trigger webhooks
    webhook_manager.trigger_event(event, kwargs)


# Export
__all__ = [
    'WebhookEvent',
    'Webhook',
    'WebhookManager',
    'webhook_manager',
    'EventEmitter',
    'event_emitter',
    'emit_event'
]
