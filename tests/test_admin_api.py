"""
Unit tests for Admin API
"""

import pytest
import json
import sys
sys.path.insert(0, '.')

from webcms.admin.admin_api import AdminAPI
from webcms.core.request import Request
from webcms.core.response import Response


class MockRequest:
    """Mock request for testing."""
    def __init__(self, method='GET', json_data=None, user_id='admin'):
        self.method = method
        self.json = json_data or {}
        self.files = {}
        self.user_id = user_id


@pytest.fixture
def api():
    """Create AdminAPI instance for testing."""
    return AdminAPI(db=None, auth=None)


@pytest.fixture
def mock_get_request():
    """Create GET request."""
    return MockRequest('GET')


@pytest.fixture
def mock_post_request():
    """Create POST request."""
    return MockRequest('POST')


class TestDashboard:
    """Test dashboard endpoints."""
    
    def test_dashboard_returns_widgets(self, api, mock_get_request):
        """Test dashboard returns widgets."""
        response = api.dashboard(mock_get_request)
        
        assert isinstance(response, Response)
        
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        assert 'widgets' in body
        assert len(body['widgets']) > 0
    
    def test_dashboard_has_required_widgets(self, api, mock_get_request):
        """Test dashboard has required widget types."""
        response = api.dashboard(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        widget_ids = [w['id'] for w in body['widgets']]
        assert 'stats' in widget_ids
        assert 'activity' in widget_ids
        assert 'health' in widget_ids


class TestSettings:
    """Test settings endpoints."""
    
    def test_get_settings_returns_defaults(self, api, mock_get_request):
        """Test get_settings returns default values."""
        response = api.get_settings(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'settings' in body
        assert 'site_name' in body['settings']
        assert body['settings']['site_name'] == 'WebCMS'
    
    def test_update_settings_returns_success(self, api):
        """Test update_settings returns success."""
        request = MockRequest('PUT', {'site_name': 'Test Site'})
        response = api.update_settings(request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert body['updated'] is True
        assert body['settings']['site_name'] == 'Test Site'
    
    def test_update_settings_handles_empty_data(self, api, mock_post_request):
        """Test update_settings handles empty data."""
        mock_post_request.json = {}
        response = api.update_settings(mock_post_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert body['updated'] is True


class TestUsers:
    """Test user endpoints."""
    
    def test_list_users_returns_list(self, api, mock_get_request):
        """Test list_users returns users list."""
        response = api.list_users(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'users' in body
        assert isinstance(body['users'], list)
    
    def test_create_user_returns_created(self, api):
        """Test create_user returns created user."""
        request = MockRequest('POST', {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        response = api.create_user(request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'id' in body
        assert body['username'] == 'testuser'


class TestRoles:
    """Test role endpoints."""
    
    def test_list_roles_returns_list(self, api, mock_get_request):
        """Test list_roles returns roles list."""
        response = api.list_roles(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'roles' in body
        assert isinstance(body['roles'], list)
    
    def test_create_role_returns_created(self, api):
        """Test create_role returns created role."""
        request = MockRequest('POST', {
            'name': 'testrole',
            'description': 'Test Role',
            'permissions': ['content:read']
        })
        response = api.create_role(request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'id' in body
        assert body['name'] == 'testrole'


class TestContent:
    """Test content endpoints."""
    
    def test_list_pages_returns_list(self, api, mock_get_request):
        """Test list_pages returns pages list."""
        response = api.list_pages(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'pages' in body
        assert isinstance(body['pages'], list)
    
    def test_list_posts_returns_list(self, api, mock_get_request):
        """Test list_posts returns posts list."""
        response = api.list_posts(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'posts' in body
        assert isinstance(body['posts'], list)
    
    def test_create_page_returns_created(self, api):
        """Test create_page returns created page."""
        request = MockRequest('POST', {
            'title': 'Test Page',
            'slug': 'test-page',
            'content': 'Test content'
        })
        response = api.create_page(request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'id' in body
        assert body['title'] == 'Test Page'


class TestMedia:
    """Test media endpoints."""
    
    def test_list_media_returns_list(self, api, mock_get_request):
        """Test list_media returns media list."""
        response = api.list_media(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'media' in body
        assert isinstance(body['media'], list)


class TestPlugins:
    """Test plugin endpoints."""
    
    def test_list_plugins_returns_list(self, api, mock_get_request):
        """Test list_plugins returns plugins list."""
        response = api.list_plugins(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'plugins' in body
        assert isinstance(body['plugins'], list)


class TestTemplates:
    """Test template endpoints."""
    
    def test_list_templates_returns_list(self, api, mock_get_request):
        """Test list_templates returns templates list."""
        response = api.list_templates(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'templates' in body
        assert isinstance(body['templates'], list)


class TestThemes:
    """Test theme endpoints."""
    
    def test_list_themes_returns_list(self, api, mock_get_request):
        """Test list_themes returns themes list."""
        response = api.list_themes(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'themes' in body
        assert isinstance(body['themes'], list)


class TestCache:
    """Test cache endpoints."""
    
    def test_cache_stats_returns_stats(self, api, mock_get_request):
        """Test cache_stats returns cache statistics."""
        response = api.cache_stats(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'keys' in body
        assert 'hit_rate' in body


class TestBackups:
    """Test backup endpoints."""
    
    def test_list_backups_returns_list(self, api, mock_get_request):
        """Test list_backups returns backups list."""
        response = api.list_backups(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'backups' in body
        assert isinstance(body['backups'], list)


class TestTenants:
    """Test tenant endpoints."""
    
    def test_list_tenants_returns_list(self, api, mock_get_request):
        """Test list_tenants returns tenants list."""
        response = api.list_tenants(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'tenants' in body
        assert isinstance(body['tenants'], list)


class TestSearch:
    """Test search endpoints."""
    
    def test_search_analytics_returns_stats(self, api, mock_get_request):
        """Test search_analytics returns search statistics."""
        response = api.search_analytics(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'queries_24h' in body


class TestNotifications:
    """Test notification endpoints."""
    
    def test_get_notification_preferences_returns_preferences(self, api, mock_get_request):
        """Test get_notification_preferences returns preferences."""
        response = api.get_notification_preferences(mock_get_request)
        body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
        
        assert 'preferences' in body


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
