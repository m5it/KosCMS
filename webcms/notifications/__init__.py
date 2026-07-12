"""
Notification system for WebCMS

Email, in-app, and push notifications with templates and queues.
"""

from .templates import TemplateEngine
from .adapters import SMTPAdapter, SendGridAdapter
from .preferences import NotificationPreferences
from .queue import EmailQueue
from .manager import NotificationManager
from .api import NotificationAPI

__all__ = [
    "TemplateEngine",
    "SMTPAdapter",
    "SendGridAdapter",
    "NotificationPreferences",
    "EmailQueue",
    "NotificationManager",
    "NotificationAPI"
]
