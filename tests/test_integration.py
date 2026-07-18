#!/usr/bin/env python3
"""
Integration Tests for WebCMS Admin Panel

Tests the complete system integration
"""

import unittest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from webcms.admin.admin_api import AdminAPI
from webcms.client import WebCMSAdminClient
from webcms.health import health
from webcms.i18n import i18n
from webcms.graphql_api import execute_graphql


class TestSystemIntegration(unittest.TestCase):
    """Test complete system integration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.api = AdminAPI(db=None, auth=None)
    
    def test_all_modules_import(self):
        """Test all modules can be imported."""
        modules = [
            'webcms.admin.admin_api',
            'webcms.admin.logging_middleware',
            'webcms.admin.performance_monitor',
            'webcms.admin.rate_limiter',
            'webcms.admin.validators',
            'webcms.admin.data_import_export',
            'webcms.admin.webhooks',
            'webcms.admin.scheduler',
            'webcms.cache.manager',
            'webcms.cli',
            'webcms.client',
            'webcms.health',
            'webcms.i18n',
            'webcms.api_versioning',
            'webcms.migrations',
            'webcms.graphql_api',
            'webcms.content_versioning',
            'webcms.realtime',
            'webcms.advanced_search',
            'webcms.email_templates',
            'webcms.analytics',
            'webcms.dev_tools',
        ]
        
        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                self.fail(f"Failed to import {module}: {e}")
    
    def test_admin_api_endpoints(self):
        """Test all admin API endpoints respond."""
        class MockRequest:
            method = 'GET'
            json = {}
            files = {}
        
        endpoints = [
            ('dashboard', []),
            ('list_users', []),
            ('list_roles', []),
            ('list_pages', []),
            ('list_posts', []),
            ('list_media', []),
            ('list_plugins', []),
            ('list_templates', []),
            ('list_themes', []),
            ('list_backups', []),
            ('list_tenants', []),
            ('cache_stats', []),
            ('search_analytics', []),
            ('get_notification_preferences', []),
            ('get_settings', []),
        ]
        
        for endpoint_name, args in endpoints:
            with self.subTest(endpoint=endpoint_name):
                method = getattr(self.api, endpoint_name)
                req = MockRequest()
                response = method(req)
                self.assertIsNotNone(response)
                self.assertIn(response.status_code, [200, 201, 204])
    
    def test_health_check(self):
        """Test health check system."""
        response = health.get_status()
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.body)
        self.assertIn('status', data)
        self.assertIn('checks', data)
    
    def test_i18n_system(self):
        """Test internationalization."""
        # Test English translations
        result = i18n.t('common.save')
        self.assertEqual(result, 'Save')
        
        result = i18n.t('user.username')
        self.assertEqual(result, 'Username')
    
    def test_graphql_execution(self):
        """Test GraphQL query execution."""
        result = execute_graphql('{ users { id username } }')
        self.assertIn('data', result)
    
    def test_sdk_client_creation(self):
        """Test SDK client can be created."""
        client = WebCMSAdminClient(
            base_url='http://localhost:5000',
            api_key='test-key'
        )
        self.assertIsNotNone(client)
        self.assertEqual(client.base_url, 'http://localhost:5000')


class TestDataFlow(unittest.TestCase):
    """Test data flow through the system."""
    
    def test_content_creation_flow(self):
        """Test complete content creation flow."""
        api = AdminAPI(db=None, auth=None)
        
        class MockRequest:
            def __init__(self, method='POST', data=None):
                self.method = method
                self.json = data or {}
                self.files = {}
        
        # Create page
        create_req = MockRequest('POST', {
            'title': 'Test Page',
            'slug': 'test-page',
            'content': 'Test content'
        })
        
        response = api.create_page(create_req)
        self.assertEqual(response.status_code, 201)
        
        # Get settings
        settings_req = MockRequest('GET')
        response = api.get_settings(settings_req)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.body)
        self.assertIn('settings', data)


class TestSecurity(unittest.TestCase):
    """Test security features."""
    
    def test_rate_limiter(self):
        """Test rate limiting."""
        from webcms.admin.rate_limiter import RateLimiter
        
        limiter = RateLimiter()
        limiter.set_limit('test', 5, 60)
        
        # Should allow first 5 requests
        for i in range(5):
            self.assertTrue(limiter.is_allowed(f'user_{i}', 'test'))
    
    def test_validators(self):
        """Test input validators."""
        from webcms.admin.validators import EmailValidator, StringValidator
        
        email_val = EmailValidator()
        result = email_val.validate('test@example.com', 'email')
        self.assertEqual(result, 'test@example.com')
        
        string_val = StringValidator(min_length=3, max_length=10)
        result = string_val.validate('hello', 'name')
        self.assertEqual(result, 'hello')


class TestPerformance(unittest.TestCase):
    """Test performance features."""
    
    def test_performance_monitor(self):
        """Test performance monitoring."""
        from webcms.admin.performance_monitor import monitor
        
        # Record some metrics
        monitor.record('test_endpoint', 0.1)
        
        stats = monitor.get_stats('test_endpoint')
        self.assertIn('count', stats)
        self.assertEqual(stats['count'], 1)


class TestExportImport(unittest.TestCase):
    """Test data export/import."""
    
    def test_export_import(self):
        """Test export and import functionality."""
        from webcms.admin.data_import_export import DataExporter, DataImporter, DataFormat
        
        # Test export
        exporter = DataExporter()
        data = [{'id': '1', 'name': 'Test'}]
        result = exporter.export(data, DataFormat.JSON)
        
        self.assertTrue(result.success)
        self.assertEqual(result.record_count, 1)
        
        # Test import
        importer = DataImporter()
        result = importer.import_data(result.data, DataFormat.JSON, 'test')
        self.assertEqual(result.imported, 1)


def run_integration_tests():
    """Run all integration tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestSystemIntegration,
        TestDataFlow,
        TestSecurity,
        TestPerformance,
        TestExportImport,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)
