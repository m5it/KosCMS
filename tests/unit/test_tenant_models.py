#!/usr/bin/env python3
"""Unit tests for tenant models."""

from webcms.tenants.models import Tenant, TenantQuota


def test_tenant_quota_to_dict():
    quota = TenantQuota(max_posts=500)
    assert quota.to_dict()["max_posts"] == 500


def test_tenant_plugins():
    tenant = Tenant(name="Test", slug="test")
    tenant.add_plugin("seo")
    assert "seo" in tenant.plugins
    tenant.remove_plugin("seo")
    assert "seo" not in tenant.plugins


def test_tenant_theme():
    tenant = Tenant(name="Test", slug="test")
    tenant.set_theme("dark")
    assert tenant.theme == "dark"
