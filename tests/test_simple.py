#!/usr/bin/env python3
"""
Simple verification tests
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestImports(unittest.TestCase):
    """Test all modules import correctly."""
    
    def test_admin_modules(self):
        """Test admin modules."""
        from webcms.admin.admin_api import AdminAPI
        from webcms.admin.logging_middleware import AdminLogger
        from webcms.admin.performance_monitor import monitor
        from webcms.admin.rate_limiter import RateLimiter
        from webcms.admin.validators import EmailValidator
        
        self.assertTrue(True)
    
    def test_core_modules(self):
        """Test core modules."""
        from webcms.cache.manager import CacheManager
        from webcms.cli import cli
        from webcms.client import WebCMSAdminClient
        from webcms.health import health
        from webcms.i18n import i18n
        
        self.assertTrue(True)
    
    def test_advanced_modules(self):
        """Test advanced modules."""
        from webcms.graphql_api import execute_graphql
        from webcms.content_versioning import version_manager
        from webcms.realtime import realtime_manager
        from webcms.advanced_search import search_manager
        from webcms.analytics import analytics_manager
        
        self.assertTrue(True)


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality."""
    
    def test_health_check(self):
        """Test health check."""
        from webcms.health import health
        response = health.get_status()
        self.assertEqual(response.status, 200)
    
    def test_i18n(self):
        """Test i18n."""
        from webcms.i18n import i18n
        result = i18n.t('common.save')
        self.assertEqual(result, 'Save')
    
    def test_graphql(self):
        """Test GraphQL."""
        from webcms.graphql_api import execute_graphql
        result = execute_graphql('{ users { id } }')
        self.assertIn('data', result)
    
    def test_admin_api(self):
        """Test AdminAPI."""
        from webcms.admin.admin_api import AdminAPI
        
        class MockRequest:
            method = 'GET'
            json = {}
            files = {}
        
        api = AdminAPI(db=None, auth=None)
        response = api.dashboard(MockRequest())
        self.assertEqual(response.status, 200)


if __name__ == '__main__':
    unittest.main(verbosity=2)
