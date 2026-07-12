"""
Tenant manager with CRUD, sharing, and analytics.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from .models import Tenant, TenantQuota
from .router import TenantRouter


class TenantManager:
    """Manages tenants and their resources."""

    def __init__(self, storage=None):
        self.storage = storage or {}
        self.router = TenantRouter()
        self._tenants: Dict[str, Tenant] = {}

    async def create_tenant(self, name: str, slug: str, domain: str,
                          schema_name: str = None, theme: str = "default",
                          quotas: Optional[TenantQuota] = None) -> Tenant:
        """Create new tenant."""
        tenant = Tenant(
            tenant_id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            domain=domain,
            schema_name=schema_name or f"tenant_{slug}",
            theme=theme,
            quotas=quotas or TenantQuota()
        )
        self._tenants[tenant.tenant_id] = tenant
        return tenant

    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self._tenants.get(tenant_id)

    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        for tenant in self._tenants.values():
            if tenant.domain == domain:
                return tenant
        return None

    async def list_tenants(self) -> List[Tenant]:
        """List all tenants."""
        return list(self._tenants.values())

    async def update_tenant(self, tenant_id: str, updates: Dict) -> Optional[Tenant]:
        """Update tenant settings."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return None
        if "name" in updates:
            tenant.name = updates["name"]
        if "domain" in updates:
            tenant.domain = updates["domain"]
        if "theme" in updates:
            tenant.theme = updates["theme"]
        if "is_active" in updates:
            tenant.is_active = updates["is_active"]
        if "plugins" in updates:
            tenant.plugins = updates["plugins"]
        if "settings" in updates:
            tenant.update_settings(updates["settings"])
        if "quotas" in updates:
            tenant.quotas = TenantQuota(**updates["quotas"])
        return tenant

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant."""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False

    async def set_tenant_theme(self, tenant_id: str, theme: str) -> Optional[Tenant]:
        """Set tenant theme."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.set_theme(theme)
        return tenant

    async def add_tenant_plugin(self, tenant_id: str, plugin_id: str) -> Optional[Tenant]:
        """Add plugin to tenant."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.add_plugin(plugin_id)
        return tenant

    async def remove_tenant_plugin(self, tenant_id: str, plugin_id: str) -> Optional[Tenant]:
        """Remove plugin from tenant."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.remove_plugin(plugin_id)
        return tenant

    async def share_content(self, source_tenant_id: str, target_tenant_id: str,
                            content_id: str, content_type: str = "post") -> Dict:
        """Share content across tenants."""
        source = await self.get_tenant(source_tenant_id)
        target = await self.get_tenant(target_tenant_id)
        if not source or not target:
            return {"error": "Tenant not found"}

        share_id = str(uuid.uuid4())
        return {
            "share_id": share_id,
            "source_tenant_id": source_tenant_id,
            "target_tenant_id": target_tenant_id,
            "content_id": content_id,
            "content_type": content_type,
            "shared_at": datetime.utcnow().isoformat()
        }

    async def get_analytics(self, tenant_id: str) -> Dict:
        """Get tenant analytics."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "posts_used": 0,
            "pages_used": 0,
            "users_used": 0,
            "storage_used_mb": 0,
            "quotas": tenant.quotas.to_dict(),
            "active_plugins": tenant.plugins,
            "theme": tenant.theme
        }

    async def backup_tenant(self, tenant_id: str) -> Dict:
        """Backup tenant configuration."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        return {
            "tenant_id": tenant_id,
            "backup_id": str(uuid.uuid4()),
            "data": tenant.to_dict(),
            "created_at": datetime.utcnow().isoformat()
        }

    async def restore_tenant(self, tenant_id: str, backup_data: Dict) -> Optional[Tenant]:
        """Restore tenant from backup."""
        try:
            tenant = Tenant(
                tenant_id=tenant_id,
                name=backup_data.get("name", "Restored Tenant"),
                slug=backup_data.get("slug", "restored"),
                domain=backup_data.get("domain", "localhost"),
                schema_name=backup_data.get("schema_name", "public"),
                theme=backup_data.get("theme", "default"),
                plugins=backup_data.get("plugins", []),
                is_active=backup_data.get("is_active", True),
                quotas=TenantQuota(**backup_data.get("quotas", {})),
                settings=backup_data.get("settings", {}),
                created_at=datetime.fromisoformat(backup_data.get("created_at")) if backup_data.get("created_at") else datetime.utcnow()
            )
            self._tenants[tenant_id] = tenant
            return tenant
        except Exception as e:
            return None

    async def check_quota(self, tenant_id: str, resource: str) -> Dict:
        """Check quota status."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}

        quota_value = getattr(tenant.quotas, f"max_{resource}", 0)
        return {
            "resource": resource,
            "limit": quota_value,
            "used": 0,
            "available": quota_value,
            "exceeded": False
        }
