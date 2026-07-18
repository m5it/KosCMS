#!/usr/bin/env python3
"""
End-to-End Tests for Admin Panel
"""

import sys
import json
sys.path.insert(0, '.')

from webcms.admin.admin_api import AdminAPI
from webcms.admin.logging_middleware import AdminLogger, AuditTrail


class MockRequest:
    """Mock request for testing."""
    def __init__(self, method='GET', json_data=None, user_id='admin'):
        self.method = method
        self.json = json_data or {}
        self.files = {}
        self.user_id = user_id


def run_tests():
    """Run all admin panel tests."""
    print("=" * 70)
    print("ADMIN PANEL END-TO-END TESTS")
    print("=" * 70)
    
    api = AdminAPI(db=None, auth=None)
    passed = 0
    failed = 0
    
    # Test 1: Dashboard
    print("\n1. Testing Dashboard...")
    try:
        req = MockRequest('GET')
        resp = api.dashboard(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'widgets' in body, "Dashboard should return widgets"
        print("   ✅ Dashboard works")
        passed += 1
    except Exception as e:
        print(f"   ❌ Dashboard failed: {e}")
        failed += 1
    
    # Test 2: Settings Get
    print("\n2. Testing Settings Get...")
    try:
        req = MockRequest('GET')
        resp = api.get_settings(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'settings' in body, "Should return settings"
        assert 'site_name' in body['settings'], "Should have site_name"
        print(f"   ✅ Settings get works (site_name: {body['settings']['site_name']})")
        passed += 1
    except Exception as e:
        print(f"   ❌ Settings get failed: {e}")
        failed += 1
    
    # Test 3: Settings Update
    print("\n3. Testing Settings Update...")
    try:
        req = MockRequest('PUT', {'site_name': 'Test Site'})
        resp = api.update_settings(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert body.get('updated') == True, "Should return updated=True"
        assert body['settings']['site_name'] == 'Test Site', "Should save site_name"
        print(f"   ✅ Settings update works")
        passed += 1
    except Exception as e:
        print(f"   ❌ Settings update failed: {e}")
        failed += 1
    
    # Test 4: List Users
    print("\n4. Testing List Users...")
    try:
        req = MockRequest('GET')
        resp = api.list_users(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'users' in body, "Should return users list"
        print(f"   ✅ List users works ({len(body['users'])} users)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List users failed: {e}")
        failed += 1
    
    # Test 5: List Roles
    print("\n5. Testing List Roles...")
    try:
        req = MockRequest('GET')
        resp = api.list_roles(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'roles' in body, "Should return roles list"
        print(f"   ✅ List roles works ({len(body['roles'])} roles)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List roles failed: {e}")
        failed += 1
    
    # Test 6: List Pages
    print("\n6. Testing List Pages...")
    try:
        req = MockRequest('GET')
        resp = api.list_pages(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'pages' in body, "Should return pages list"
        print(f"   ✅ List pages works ({len(body['pages'])} pages)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List pages failed: {e}")
        failed += 1
    
    # Test 7: List Posts
    print("\n7. Testing List Posts...")
    try:
        req = MockRequest('GET')
        resp = api.list_posts(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'posts' in body, "Should return posts list"
        print(f"   ✅ List posts works ({len(body['posts'])} posts)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List posts failed: {e}")
        failed += 1
    
    # Test 8: List Media
    print("\n8. Testing List Media...")
    try:
        req = MockRequest('GET')
        resp = api.list_media(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'media' in body, "Should return media list"
        print(f"   ✅ List media works ({len(body['media'])} items)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List media failed: {e}")
        failed += 1
    
    # Test 9: List Plugins
    print("\n9. Testing List Plugins...")
    try:
        req = MockRequest('GET')
        resp = api.list_plugins(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'plugins' in body, "Should return plugins list"
        print(f"   ✅ List plugins works ({len(body['plugins'])} plugins)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List plugins failed: {e}")
        failed += 1
    
    # Test 10: List Templates
    print("\n10. Testing List Templates...")
    try:
        req = MockRequest('GET')
        resp = api.list_templates(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'templates' in body, "Should return templates list"
        print(f"   ✅ List templates works ({len(body['templates'])} templates)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List templates failed: {e}")
        failed += 1
    
    # Test 11: List Themes
    print("\n11. Testing List Themes...")
    try:
        req = MockRequest('GET')
        resp = api.list_themes(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'themes' in body, "Should return themes list"
        print(f"   ✅ List themes works ({len(body['themes'])} themes)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List themes failed: {e}")
        failed += 1
    
    # Test 12: Cache Stats
    print("\n12. Testing Cache Stats...")
    try:
        req = MockRequest('GET')
        resp = api.cache_stats(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'keys' in body, "Should return cache stats"
        print(f"   ✅ Cache stats works ({body['keys']} keys)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Cache stats failed: {e}")
        failed += 1
    
    # Test 13: List Backups
    print("\n13. Testing List Backups...")
    try:
        req = MockRequest('GET')
        resp = api.list_backups(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'backups' in body, "Should return backups list"
        print(f"   ✅ List backups works ({len(body['backups'])} backups)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List backups failed: {e}")
        failed += 1
    
    # Test 14: List Tenants
    print("\n14. Testing List Tenants...")
    try:
        req = MockRequest('GET')
        resp = api.list_tenants(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'tenants' in body, "Should return tenants list"
        print(f"   ✅ List tenants works ({len(body['tenants'])} tenants)")
        passed += 1
    except Exception as e:
        print(f"   ❌ List tenants failed: {e}")
        failed += 1
    
    # Test 15: Search Analytics
    print("\n15. Testing Search Analytics...")
    try:
        req = MockRequest('GET')
        resp = api.search_analytics(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'queries_24h' in body, "Should return search analytics"
        print(f"   ✅ Search analytics works ({body['queries_24h']} queries)")
        passed += 1
    except Exception as e:
        print(f"   ❌ Search analytics failed: {e}")
        failed += 1
    
    # Test 16: Notification Preferences
    print("\n16. Testing Notification Preferences...")
    try:
        req = MockRequest('GET')
        resp = api.get_notification_preferences(req)
        body = json.loads(resp.body.decode('utf-8')) if isinstance(resp.body, bytes) else resp.body
        assert 'preferences' in body, "Should return preferences"
        print(f"   ✅ Notification preferences works")
        passed += 1
    except Exception as e:
        print(f"   ❌ Notification preferences failed: {e}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{passed+failed} tests passed")
    print("=" * 70)
    
    if failed == 0:
        print("🎉 ALL END-TO-END TESTS PASSED! 🎉")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
