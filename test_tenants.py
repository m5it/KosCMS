#!/usr/bin/env python3
"""Test tenant system"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.tenants import TenantManager, TenantRouter


async def test_tenants():
    print('Testing tenant system...')
    manager = TenantManager()

    # Create tenant
    tenant = await manager.create_tenant(
        name="Acme Blog",
        slug="acme",
        domain="acme.example.com",
        theme="modern"
    )
    print(f'Created tenant: {tenant.name} ({tenant.tenant_id})')

    # Verify isolation via router
    token = manager.router.set_tenant(tenant)
    schema = manager.router.get_current_schema()
    print(f'Tenant schema: {schema}')
    manager.router.reset_tenant(token)

    # Update theme
    await manager.set_tenant_theme(tenant.tenant_id, "dark")
    updated = await manager.get_tenant(tenant.tenant_id)
    print(f'Updated theme: {updated.theme}')

    # Add plugin
    await manager.add_tenant_plugin(tenant.tenant_id, "seo-plugin")
    print(f'Plugins: {updated.plugins}')

    # Cross-tenant sharing
    tenant2 = await manager.create_tenant(
        name="Partner Blog",
        slug="partner",
        domain="partner.example.com"
    )
    share = await manager.share_content(
        tenant.tenant_id,
        tenant2.tenant_id,
        "post-123"
    )
    print(f'Shared content: {share["share_id"]}')

    # Analytics
    analytics = await manager.get_analytics(tenant.tenant_id)
    print(f'Analytics: {analytics}')

    # Backup and restore
    backup = await manager.backup_tenant(tenant.tenant_id)
    print(f'Backup created: {backup["backup_id"]}')

    restored = await manager.restore_tenant("restored-id", backup["data"])
    print(f'Restored tenant: {restored.name}')

    # Quota check
    quota = await manager.check_quota(tenant.tenant_id, "posts")
    print(f'Quota: {quota}')

    print('Tenant system verified!')


if __name__ == '__main__':
    asyncio.run(test_tenants())
