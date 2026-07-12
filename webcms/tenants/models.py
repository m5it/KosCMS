"""
Tenant models with isolation and quotas.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional


class TenantQuota:
    """Resource limits for a tenant."""

    def __init__(self, max_posts=1000, max_pages=100, max_users=50,
                 max_storage_mb=1024, max_bandwidth_gb=100):
        self.max_posts = max_posts
        self.max_pages = max_pages
        self.max_users = max_users
        self.max_storage_mb = max_storage_mb
        self.max_bandwidth_gb = max_bandwidth_gb

    def to_dict(self):
        return {
            "max_posts": self.max_posts,
            "max_pages": self.max_pages,
            "max_users": self.max_users,
            "max_storage_mb": self.max_storage_mb,
            "max_bandwidth_gb": self.max_bandwidth_gb
        }


class Tenant:
    """Tenant model with isolation."""

    def __init__(self, tenant_id=None, name=None, slug=None, domain=None,
                 schema_name="public", theme="default", plugins=None,
                 is_active=True, quotas=None, settings=None, created_at=None):
        self.tenant_id = tenant_id or str(uuid.uuid4())
        self.name = name or "Default Tenant"
        self.slug = slug or "default"
        self.domain = domain or "localhost"
        self.schema_name = schema_name
        self.theme = theme or "default"
        self.plugins = plugins or []
        self.is_active = is_active
        self.quotas = quotas or TenantQuota()
        self.settings = settings or {}
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "domain": self.domain,
            "schema_name": self.schema_name,
            "theme": self.theme,
            "plugins": self.plugins,
            "is_active": self.is_active,
            "quotas": self.quotas.to_dict(),
            "settings": self.settings,
            "created_at": self.created_at.isoformat()
        }

    def add_plugin(self, plugin_id: str):
        if plugin_id not in self.plugins:
            self.plugins.append(plugin_id)

    def remove_plugin(self, plugin_id: str):
        if plugin_id in self.plugins:
            self.plugins.remove(plugin_id)

    def set_theme(self, theme: str):
        self.theme = theme

    def update_settings(self, settings: Dict):
        self.settings.update(settings)
