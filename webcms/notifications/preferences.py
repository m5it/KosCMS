"""
Notification preferences per user.
"""

from typing import Dict, List


class NotificationPreferences:
    """User notification preferences."""

    def __init__(self):
        self._prefs: Dict[str, Dict] = {}

    def get_defaults(self) -> Dict:
        """Get default preferences."""
        return {
            "email": {
                "enabled": True,
                "digest": "daily",
                "workflow": True,
                "comments": True,
                "mentions": True
            },
            "in_app": {
                "enabled": True,
                "workflow": True,
                "comments": True,
                "mentions": True
            },
            "push": {
                "enabled": False,
                "workflow": True,
                "mentions": True
            }
        }

    def get_preferences(self, user_id: str) -> Dict:
        """Get user preferences."""
        if user_id not in self._prefs:
            self._prefs[user_id] = self.get_defaults()
        return self._prefs[user_id]

    def update_preferences(self, user_id: str, updates: Dict) -> Dict:
        """Update user preferences."""
        prefs = self.get_preferences(user_id)
        for channel, settings in updates.items():
            if channel in prefs:
                prefs[channel].update(settings)
        return prefs

    def is_enabled(self, user_id: str, channel: str, event_type: str) -> bool:
        """Check if notification channel is enabled for event type."""
        prefs = self.get_preferences(user_id)
        channel_prefs = prefs.get(channel, {})
        if not channel_prefs.get("enabled", False):
            return False
        return channel_prefs.get(event_type, True)

    def get_digest_users(self, digest_type: str) -> List[str]:
        """Get users who want a specific digest."""
        users = []
        for user_id, prefs in self._prefs.items():
            email_prefs = prefs.get("email", {})
            if email_prefs.get("enabled") and email_prefs.get("digest") == digest_type:
                users.append(user_id)
        return users
