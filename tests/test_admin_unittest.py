#!/usr/bin/env python3
"""
Unit tests for Admin API using Python's built-in unittest
No external dependencies required
"""

import unittest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webcms.admin.admin_api import AdminAPI
from webcms.core.response import Response


class MockRequest:
    """Mock request for testing."""
    def __init__(self, method='GET', json_data=None, user_id='admin'):
        self.method = method
        self.json = json_data or {}
        self.files = {}
        self.user_id = user_id


def parse_response(response):
    """Parse response body to dict."""
    if isinstance(response.body, bytes):
        return json.loads(response.body.decode('utf-8'))
    elif isinstance(response.body, str):
        return json.loads(response.body)
    return response.body


class TestDashboard(unittest.TestCase):
    """Test dashboard endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
        self.request = MockRequest('GET')
    
    def test_dashboard_returns_widgets(self):
        """Test dashboard returns widgets."""
        response = self.api.dashboard(self.request)
        self.assertIsInstance(response, Response)
        
        body = parse_response(response)
        self.assertIn('widgets', body)
        self.assertGreater(len(body['widgets']), 0)
    
    def test_dashboard_has_required_widgets(self):
        """Test dashboard has required widget types."""
        response = self.api.dashboard(self.request)
        body = parse_response(response)
        
        widget_ids = [w['id'] for w in body['widgets']]
        self.assertIn('stats', widget_ids)
        self.assertIn('activity', widget_ids)
        self.assertIn('health', widget_ids)


class TestSettings(unittest.TestCase):
    """Test settings endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_get_settings_returns_defaults(self):
        """Test get_settings returns default values."""
        request = MockRequest('GET')
        response = self.api.get_settings(request)
        body = parse_response(response)
        
        self.assertIn('settings', body)
        self.assertIn('site_name', body['settings'])
        self.assertEqual(body['settings']['site_name'], 'WebCMS')
    
    def test_update_settings_returns_success(self):
        """Test update_settings returns success."""
        request = MockRequest('PUT', {'site_name': 'Test Site'})
        response = self.api.update_settings(request)
        body = parse_response(response)
        
        self.assertTrue(body['updated'])
        self.assertEqual(body['settings']['site_name'], 'Test Site')
    
    def test_update_settings_handles_empty_data(self):
        """Test update_settings handles empty data."""
        request = MockRequest('PUT', {})
        response = self.api.update_settings(request)
        body = parse_response(response)
        
        self.assertTrue(body['updated'])


class TestUsers(unittest.TestCase):
    """Test user endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_users_returns_list(self):
        """Test list_users returns users list."""
        request = MockRequest('GET')
        response = self.api.list_users(request)
        body = parse_response(response)
        
        self.assertIn('users', body)
        self.assertIsInstance(body['users'], list)
    
    def test_create_user_returns_success(self):
        """Test create_user returns success with id."""
        request = MockRequest('POST', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        response = self.api.create_user(request)
        body = parse_response(response)
        
        # API returns {id: uuid, created: True}
        self.assertIn('id', body)
        self.assertTrue(body['created'])


class TestRoles(unittest.TestCase):
    """Test role endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_roles_returns_list(self):
        """Test list_roles returns roles list."""
        request = MockRequest('GET')
        response = self.api.list_roles(request)
        body = parse_response(response)
        
        self.assertIn('roles', body)
        self.assertIsInstance(body['roles'], list)
    
    def test_create_role_returns_success(self):
        """Test create_role returns success with id."""
        request = MockRequest('POST', {
            'name': 'testrole',
            'description': 'Test Role',
            'permissions': ['content:read']
        })
        response = self.api.create_role(request)
        body = parse_response(response)
        
        # API returns {id: uuid, created: True}
        self.assertIn('id', body)
        self.assertTrue(body['created'])


class TestContent(unittest.TestCase):
    """Test content endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_pages_returns_list(self):
        """Test list_pages returns pages list."""
        request = MockRequest('GET')
        response = self.api.list_pages(request)
        body = parse_response(response)
        
        self.assertIn('pages', body)
        self.assertIsInstance(body['pages'], list)
    
    def test_list_posts_returns_list(self):
        """Test list_posts returns posts list."""
        request = MockRequest('GET')
        response = self.api.list_posts(request)
        body = parse_response(response)
        
        self.assertIn('posts', body)
        self.assertIsInstance(body['posts'], list)
    
    def test_create_page_returns_success(self):
        """Test create_page returns success with id."""
        request = MockRequest('POST', {
            'title': 'Test Page',
            'slug': 'test-page',
            'content': 'Test content'
        })
        response = self.api.create_page(request)
        body = parse_response(response)
        
        # API returns {id: uuid, created: True}
        self.assertIn('id', body)
        self.assertTrue(body['created'])


class TestMedia(unittest.TestCase):
    """Test media endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_media_returns_list(self):
        """Test list_media returns media list."""
        request = MockRequest('GET')
        response = self.api.list_media(request)
        body = parse_response(response)
        
        self.assertIn('media', body)
        self.assertIsInstance(body['media'], list)


class TestPlugins(unittest.TestCase):
    """Test plugin endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_plugins_returns_list(self):
        """Test list_plugins returns plugins list."""
        request = MockRequest('GET')
        response = self.api.list_plugins(request)
        body = parse_response(response)
        
        self.assertIn('plugins', body)
        self.assertIsInstance(body['plugins'], list)


class TestTemplates(unittest.TestCase):
    """Test template endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_templates_returns_list(self):
        """Test list_templates returns templates list."""
        request = MockRequest('GET')
        response = self.api.list_templates(request)
        body = parse_response(response)
        
        self.assertIn('templates', body)
        self.assertIsInstance(body['templates'], list)


class TestThemes(unittest.TestCase):
    """Test theme endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_themes_returns_list(self):
        """Test list_themes returns themes list."""
        request = MockRequest('GET')
        response = self.api.list_themes(request)
        body = parse_response(response)
        
        self.assertIn('themes', body)
        self.assertIsInstance(body['themes'], list)


class TestCache(unittest.TestCase):
    """Test cache endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_cache_stats_returns_stats(self):
        """Test cache_stats returns cache statistics."""
        request = MockRequest('GET')
        response = self.api.cache_stats(request)
        body = parse_response(response)
        
        self.assertIn('keys', body)
        self.assertIn('hit_rate', body)


class TestBackups(unittest.TestCase):
    """Test backup endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_backups_returns_list(self):
        """Test list_backups returns backups list."""
        request = MockRequest('GET')
        response = self.api.list_backups(request)
        body = parse_response(response)
        
        self.assertIn('backups', body)
        self.assertIsInstance(body['backups'], list)


class TestTenants(unittest.TestCase):
    """Test tenant endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_list_tenants_returns_list(self):
        """Test list_tenants returns tenants list."""
        request = MockRequest('GET')
        response = self.api.list_tenants(request)
        body = parse_response(response)
        
        self.assertIn('tenants', body)
        self.assertIsInstance(body['tenants'], list)


class TestSearch(unittest.TestCase):
    """Test search endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_search_analytics_returns_stats(self):
        """Test search_analytics returns search statistics."""
        request = MockRequest('GET')
        response = self.api.search_analytics(request)
        body = parse_response(response)
        
        self.assertIn('queries_24h', body)


class TestNotifications(unittest.TestCase):
    """Test notification endpoints."""
    
    def setUp(self):
        self.api = AdminAPI(db=None, auth=None)
    
    def test_get_notification_preferences_returns_preferences(self):
        """Test get_notification_preferences returns preferences."""
        request = MockRequest('GET')
        response = self.api.get_notification_preferences(request)
        body = parse_response(response)
        
        self.assertIn('preferences', body)


def run_tests():
    """Run all tests with verbosity."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDashboard,
        TestSettings,
        TestUsers,
        TestRoles,
        TestContent,
        TestMedia,
        TestPlugins,
        TestTemplates,
        TestThemes,
        TestCache,
        TestBackups,
        TestTenants,
        TestSearch,
        TestNotifications
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL UNIT TESTS PASSED! 🎉")
        return 0
    else:
        print(f"\n⚠️  {len(result.failures) + len(result.errors)} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())
