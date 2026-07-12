#!/usr/bin/env python3
"""Integration tests for multi-tenant system."""

import pytest
from webcms.tenants import TenantManager


@pytest.mark.asyncio
async def test_tenant_isolation():
    manager = TenantManager()
    tenant = await manager.create_tenant(
        name="Test Tenant",
        slug="test",
        domain="test.example.com"
    )

    assert tenant.name == "Test Tenant"
    assert tenant.schema_name == "tenant_test"

    token = manager.router.set_tenant(tenant)
    schema = manager.router.get_current_schema()
    assert schema == "tenant_test"
    manager.router.reset_tenant(token)

    analytics = await manager.get_analytics(tenant.tenant_id)
    assert analytics["name"] == "Test Tenant"


@pytest.mark.asyncio
async def test_cross_tenant_sharing():
    manager = TenantManager()
    source = await manager.create_tenant("Source", "source", "source.com")
    target = await manager.create_tenant("Target", "target", "target.com")

    share = await manager.share_content(
        source.tenant_id,
        target.tenant_id,
        "post-123"
    )
    assert "share_id" in share
