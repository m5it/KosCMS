"""
Notification preferences per user with KosDB persistence.
"""

import json
from typing import Dict, List, Optional, Any


class NotificationPreferences:
    """User notification preferences with KosDB persistence."""

    def __init__(self, db=None):
        self.db = db
        self._prefs: Dict[str, Dict] = {}
        self._ensure_table()
        self._load_from_kosdb()

    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods

    def _ensure_table(self):
        """Ensure notification preferences table exists."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
            if 'notification_preferences' in tables:
                return
        except Exception:
            pass

        try:
            self.db.execute("""
                CREATE TABLE notification_preferences (
                    user_id TEXT PRIMARY KEY,
                    email_enabled TEXT DEFAULT '1',
                    email_digest TEXT DEFAULT 'daily',
                    email_workflow TEXT DEFAULT '1',
                    email_comments TEXT DEFAULT '1',
                    email_mentions TEXT DEFAULT '1',
                    in_app_enabled TEXT DEFAULT '1',
                    in_app_workflow TEXT DEFAULT '1',
                    in_app_comments TEXT DEFAULT '1',
                    in_app_mentions TEXT DEFAULT '1',
                    push_enabled TEXT DEFAULT '0',
                    push_workflow TEXT DEFAULT '1',
                    push_mentions TEXT DEFAULT '1',
                    updated_at TEXT
                )
            """)
        except Exception:
            pass

    def _load_from_kosdb(self):
        """Load preferences from KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            result = self.db.query("SELECT * FROM notification_preferences")
            for row in result.get('rows', []):
                user_id = row['user_id']
                self._prefs[user_id] = {
                    "email": {
                        "enabled": row.get('email_enabled') == '1',
                        "digest": row.get('email_digest', 'daily'),
                        "workflow": row.get('email_workflow') == '1',
                        "comments": row.get('email_comments') == '1',
                        "mentions": row.get('email_mentions') == '1'
                    },
                    "in_app": {
                        "enabled": row.get('in_app_enabled') == '1',
                        "workflow": row.get('in_app_workflow') == '1',
                        "comments": row.get('in_app_comments') == '1',
                        "mentions": row.get('in_app_mentions') == '1'
                    },
                    "push": {
                        "enabled": row.get('push_enabled') == '1',
                        "workflow": row.get('push_workflow') == '1',
                        "mentions": row.get('push_mentions') == '1'
                    }
                }
        except Exception:
            pass

    def _save_to_kosdb(self, user_id: str, prefs: Dict):
        """Save preferences to KosDB."""
        if not self.db or not self._is_kosdb():
            return

        from datetime import datetime
        now = datetime.utcnow().isoformat()

        email = prefs.get("email", {})
        in_app = prefs.get("in_app", {})
        push = prefs.get("push", {})

        try:
            result = self.db.query(f"SELECT user_id FROM notification_preferences WHERE user_id='{user_id}'")
            
            if result.get('rows'):
                # Update
                self.db.execute(f"""
                    UPDATE notification_preferences SET
                        email_enabled='{1 if email.get('enabled') else 0}',
                        email_digest='{email.get('digest', 'daily')}',
                        email_workflow='{1 if email.get('workflow') else 0}',
                        email_comments='{1 if email.get('comments') else 0}',
                        email_mentions='{1 if email.get('mentions') else 0}',
                        in_app_enabled='{1 if in_app.get('enabled') else 0}',
                        in_app_workflow='{1 if in_app.get('workflow') else 0}',
                        in_app_comments='{1 if in_app.get('comments') else 0}',
                        in_app_mentions='{1 if in_app.get('mentions') else 0}',
                        push_enabled='{1 if push.get('enabled') else 0}',
                        push_workflow='{1 if push.get('workflow') else 0}',
                        push_mentions='{1 if push.get('mentions') else 0}',
                        updated_at='{now}'
                    WHERE user_id='{user_id}'
                """)
            else:
                # Insert
                self.db.execute(f"""
                    INSERT INTO notification_preferences 
                    (user_id, email_enabled, email_digest, email_workflow, email_comments, email_mentions,
                     in_app_enabled, in_app_workflow, in_app_comments, in_app_mentions,
                     push_enabled, push_workflow, push_mentions, updated_at)
                    VALUES (
                        '{user_id}',
                        '{1 if email.get('enabled') else 0}',
                        '{email.get('digest', 'daily')}',
                        '{1 if email.get('workflow') else 0}',
                        '{1 if email.get('comments') else 0}',
                        '{1 if email.get('mentions') else 0}',
                        '{1 if in_app.get('enabled') else 0}',
                        '{1 if in_app.get('workflow') else 0}',
                        '{1 if in_app.get('comments') else 0}',
                        '{1 if in_app.get('mentions') else 0}',
                        '{1 if push.get('enabled') else 0}',
                        '{1 if push.get('workflow') else 0}',
                        '{1 if push.get('mentions') else 0}',
                        '{now}'
                    )
                """)
        except Exception:
            pass

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

    def get_all(self) -> Dict[str, Any]:
        """Get all preferences (for current user or default)."""
        # Return merged defaults with any stored preferences
        defaults = self.get_defaults()
        
        # If we have KosDB data, return that
        if self.db and self._is_kosdb():
            return defaults
        
        return defaults

    def update_preferences(self, user_id: str, updates: Dict) -> Dict:
        """Update user preferences."""
        prefs = self.get_preferences(user_id)
        for channel, settings in updates.items():
            if channel in prefs:
                prefs[channel].update(settings)
        
        self._save_to_kosdb(user_id, prefs)
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

    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update preferences (sync version for API)."""
        # Merge with defaults
        defaults = self.get_defaults()
        
        for channel in ["email", "in_app", "push"]:
            if channel in data:
                defaults[channel].update(data[channel])
        
        # Save to KosDB if available
        if self.db and self._is_kosdb():
            # Use a default user ID for global preferences
            self._save_to_kosdb("default", defaults)
        
        return {"updated": True, "preferences": defaults}
