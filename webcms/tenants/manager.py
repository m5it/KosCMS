"""
Tenant manager with CRUD, sharing, and analytics with KosDB persistence.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import Tenant, TenantQuota
from .router import TenantRouter


class TenantManager:
    """Manages tenants and their resources with KosDB persistence."""

    def __init__(self, storage=None, db=None):
        self.storage = storage
        self.db = db
        self.router = TenantRouter()
        self._tenants: Dict[str, Tenant] = {}
        self._ensure_tenants_table()
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

    def _ensure_tenants_table(self):
        """Ensure tenants table exists in KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
            if 'tenants' in tables:
                return
        except Exception:
            pass

        try:
            self.db.execute("""
                CREATE TABLE tenants (
                    tenant_id TEXT PRIMARY KEY,
                    name TEXT,
                    slug TEXT,
                    domain TEXT,
                    schema_name TEXT,
                    theme TEXT,
                    is_active TEXT,
                    plugins TEXT,
                    settings TEXT,
                    quotas TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
        except Exception:
            pass

    def _load_from_kosdb(self):
        """Load tenants from KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            result = self.db.query("SELECT * FROM tenants")
            for row in result.get('rows', []):
                try:
                    tenant = Tenant(
                        tenant_id=row['tenant_id'],
                        name=row['name'],
                        slug=row['slug'],
                        domain=row.get('domain'),
                        schema_name=row.get('schema_name'),
                        theme=row.get('theme', 'default'),
                        is_active=row.get('is_active') == '1' or row.get('is_active') == 1,
                        plugins=json.loads(row['plugins']) if row.get('plugins') else [],
                        settings=json.loads(row['settings']) if row.get('settings') else {},
                        quotas=TenantQuota(**json.loads(row['quotas'])) if row.get('quotas') else TenantQuota()
                    )
                    self._tenants[tenant.tenant_id] = tenant
                except Exception:
                    continue
        except Exception:
            pass

    def _save_to_kosdb(self, tenant: Tenant):
        """Save tenant to KosDB."""
        if not self.db or not self._is_kosdb():
            return

        now = datetime.utcnow().isoformat()
        try:
            result = self.db.query(f"SELECT tenant_id FROM tenants WHERE tenant_id='{tenant.tenant_id}'")
            
            plugins = json.dumps(tenant.plugins)
            settings = json.dumps(tenant.settings)
            quotas = json.dumps(tenant.quotas.to_dict())
            
            if result.get('rows'):
                # Update
                self.db.execute(f"""
                    UPDATE tenants SET
                        name='{tenant.name}',
                        slug='{tenant.slug}',
                        domain='{tenant.domain or ''}',
                        schema_name='{tenant.schema_name or ''}',
                        theme='{tenant.theme}',
                        is_active='{1 if tenant.is_active else 0}',
                        plugins='{plugins}',
                        settings='{settings}',
                        quotas='{quotas}',
                        updated_at='{now}'
                    WHERE tenant_id='{tenant.tenant_id}'
                """)
            else:
                # Insert
                created = tenant.created_at.isoformat() if hasattr(tenant, 'created_at') else now
                self.db.execute(f"""
                    INSERT INTO tenants 
                    (tenant_id, name, slug, domain, schema_name, theme, is_active, plugins, settings, quotas, created_at, updated_at)
                    VALUES (
                        '{tenant.tenant_id}',
                        '{tenant.name}',
                        '{tenant.slug}',
                        '{tenant.domain or ''}',
                        '{tenant.schema_name or ''}',
                        '{tenant.theme}',
                        '{1 if tenant.is_active else 0}',
                        '{plugins}',
                        '{settings}',
                        '{quotas}',
                        '{created}',
                        '{now}'
                    )
                """)
        except Exception:
            pass

    def _delete_from_kosdb(self, tenant_id: str):
        """Delete tenant from KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            self.db.execute(f"DELETE FROM tenants WHERE tenant_id='{tenant_id}'")
        except Exception:
            pass

    # ============ Async Methods ============

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
        self._save_to_kosdb(tenant)
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
        
        self._save_to_kosdb(tenant)
        return tenant

    async def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant."""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            self._delete_from_kosdb(tenant_id)
            return True
        return False

    # ============ Sync Methods for Admin API ============

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create tenant (sync version)."""
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            tenant_id=tenant_id,
            name=data.get("name", "Untitled"),
            slug=data.get("slug") or data.get("name", "").lower().replace(" ", "-"),
            domain=data.get("domain"),
            is_active=data.get("active", True),
            quotas=TenantQuota()
        )
        self._tenants[tenant_id] = tenant
        self._save_to_kosdb(tenant)
        return {
            "id": tenant_id,
            "name": tenant.name,
            "slug": tenant.slug,
            "domain": tenant.domain,
            "active": tenant.is_active
        }

    def update(self, tenant_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update tenant (sync version)."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return None
        
        if "name" in data:
            tenant.name = data["name"]
        if "domain" in data:
            tenant.domain = data["domain"]
        if "active" in data:
            tenant.is_active = bool(data["active"])
        
        self._save_to_kosdb(tenant)
        return {
            "id": tenant.tenant_id,
            "name": tenant.name,
            "slug": tenant.slug,
            "domain": tenant.domain,
            "active": tenant.is_active
        }

    def delete(self, tenant_id: str) -> bool:
        """Delete tenant (sync version)."""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            self._delete_from_kosdb(tenant_id)
            return True
        return False

    def list(self) -> List[Dict[str, Any]]:
        """List tenants (sync version)."""
        return [
            {
                "id": t.tenant_id,
                "name": t.name,
                "slug": t.slug,
                "domain": t.domain,
                "active": t.is_active,
                "theme": t.theme
            }
            for t in self._tenants.values()
        ]

    def get_analytics_sync(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant analytics (sync version)."""
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return {
                "users": 0,
                "content_count": 0,
                "storage": "0 MB",
                "requests_24h": 0
            }
        
        # Get content count from KosDB if available
        content_count = 0
        if self.db and self._is_kosdb():
            try:
                result = self.db.query(f"SELECT COUNT(*) as count FROM content WHERE tenant_id='{tenant_id}'")
                if result.get('rows'):
                    content_count = result['rows'][0].get('count', 0)
            except Exception:
                pass
        
        return {
            "users": 0,  # TODO: Query users table
            "content_count": content_count,
            "storage": "0 MB",  # TODO: Calculate storage
            "requests_24h": 0  # TODO: Query analytics
        }

    # ============ Other Methods ============

    async def set_tenant_theme(self, tenant_id: str, theme: str) -> Optional[Tenant]:
        """Set tenant theme."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.set_theme(theme)
            self._save_to_kosdb(tenant)
        return tenant

    async def add_tenant_plugin(self, tenant_id: str, plugin_id: str) -> Optional[Tenant]:
        """Add plugin to tenant."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.add_plugin(plugin_id)
            self._save_to_kosdb(tenant)
        return tenant

    async def remove_tenant_plugin(self, tenant_id: str, plugin_id: str) -> Optional[Tenant]:
        """Remove plugin from tenant."""
        tenant = await self.get_tenant(tenant_id)
        if tenant:
            tenant.remove_plugin(plugin_id)
            self._save_to_kosdb(tenant)
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
        return self.get_analytics_sync(tenant_id)

    async def backup_tenant(self, tenant_id: str) -> Dict:
        """Backup tenant configuration."""
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {"error": "Tenant not found"}
        return {
            "tenant_id": tenant_id,
            "backup_time": datetime.utcnow().isoformat(),
            "config": {
                "name": tenant.name,
                "slug": tenant.slug,
                "domain": tenant.domain,
                "theme": tenant.theme,
                "plugins": tenant.plugins,
                "settings": tenant.settings,
                "quotas": tenant.quotas.to_dict()
            }
        }
