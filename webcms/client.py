"""
WebCMS Admin API Client

Python SDK for interacting with WebCMS Admin API
"""

import json
import requests
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class APIResponse:
    """API response wrapper."""
    success: bool
    data: Any
    status_code: int
    error: Optional[str] = None


class WebCMSAdminClient:
    """
    WebCMS Admin API Client
    
    Provides convenient methods for all admin operations
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, 
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize client.
        
        Args:
            base_url: Base URL of WebCMS instance (e.g., 'https://example.com')
            api_key: API key for authentication (optional)
            username: Username for JWT authentication (optional)
            password: Password for JWT authentication (optional)
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        self._token: Optional[str] = None
        self._session = requests.Session()
        
        # Set default headers
        self._session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'WebCMS-Python-SDK/1.0'
        })
        
        if api_key:
            self._session.headers['X-API-Key'] = api_key
        
        # Authenticate if credentials provided
        if username and password:
            self._authenticate()
    
    def _authenticate(self):
        """Authenticate and get JWT token."""
        response = self._session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={'username': self.username, 'password': self.password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self._token = data.get('access_token')
            if self._token:
                self._session.headers['Authorization'] = f'Bearer {self._token}'
    
    def _request(self, method: str, endpoint: str, 
                 data: Optional[Dict] = None,
                 params: Optional[Dict] = None) -> APIResponse:
        """
        Make API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
        
        Returns:
            APIResponse with result
        """
        url = urljoin(f"{self.base_url}/", f"api/v1/admin/{endpoint.lstrip('/')}")
        
        try:
            if method.upper() == 'GET':
                response = self._session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self._session.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = self._session.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self._session.delete(url, timeout=30)
            else:
                return APIResponse(False, None, 400, f"Unsupported method: {method}")
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            success = 200 <= response.status_code < 300
            
            return APIResponse(
                success=success,
                data=response_data,
                status_code=response.status_code,
                error=None if success else response_data.get('error', 'Unknown error')
            )
            
        except requests.RequestException as e:
            return APIResponse(False, None, 0, str(e))
    
    # ==================== Dashboard ====================
    
    def get_dashboard(self) -> APIResponse:
        """Get dashboard statistics."""
        return self._request('GET', 'dashboard')
    
    # ==================== Users ====================
    
    def list_users(self, limit: int = 50, offset: int = 0) -> APIResponse:
        """List all users."""
        return self._request('GET', 'users', params={'limit': limit, 'offset': offset})
    
    def create_user(self, username: str, email: str, password: str,
                    role: str = 'user', is_active: bool = True,
                    **kwargs) -> APIResponse:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: Email address
            password: Password
            role: User role (default: 'user')
            is_active: Whether user is active
            **kwargs: Additional user fields
        
        Returns:
            APIResponse with created user data
        """
        data = {
            'username': username,
            'email': email,
            'password': password,
            'role': role,
            'is_active': is_active,
            **kwargs
        }
        return self._request('POST', 'users', data=data)
    
    def get_user(self, user_id: str) -> APIResponse:
        """Get user by ID."""
        return self._request('GET', f'users/{user_id}')
    
    def update_user(self, user_id: str, **kwargs) -> APIResponse:
        """Update user."""
        return self._request('PUT', f'users/{user_id}', data=kwargs)
    
    def delete_user(self, user_id: str) -> APIResponse:
        """Delete user."""
        return self._request('DELETE', f'users/{user_id}')
    
    # ==================== Roles ====================
    
    def list_roles(self) -> APIResponse:
        """List all roles."""
        return self._request('GET', 'roles')
    
    def create_role(self, name: str, description: str = '',
                    permissions: Optional[List[str]] = None) -> APIResponse:
        """Create a new role."""
        data = {
            'name': name,
            'description': description,
            'permissions': permissions or []
        }
        return self._request('POST', 'roles', data=data)
    
    def update_role(self, role_id: str, **kwargs) -> APIResponse:
        """Update role."""
        return self._request('PUT', f'roles/{role_id}', data=kwargs)
    
    def delete_role(self, role_id: str) -> APIResponse:
        """Delete role."""
        return self._request('DELETE', f'roles/{role_id}')
    
    # ==================== Content ====================
    
    def list_pages(self, limit: int = 50, offset: int = 0) -> APIResponse:
        """List all pages."""
        return self._request('GET', 'pages', params={'limit': limit, 'offset': offset})
    
    def create_page(self, title: str, slug: str, content: str,
                    status: str = 'draft', template: str = 'page.html',
                    **kwargs) -> APIResponse:
        """Create a new page."""
        data = {
            'title': title,
            'slug': slug,
            'content': content,
            'status': status,
            'template': template,
            **kwargs
        }
        return self._request('POST', 'pages', data=data)
    
    def get_page(self, page_id: str) -> APIResponse:
        """Get page by ID."""
        return self._request('GET', f'pages/{page_id}')
    
    def update_page(self, page_id: str, **kwargs) -> APIResponse:
        """Update page."""
        return self._request('PUT', f'pages/{page_id}', data=kwargs)
    
    def delete_page(self, page_id: str) -> APIResponse:
        """Delete page."""
        return self._request('DELETE', f'pages/{page_id}')
    
    def list_posts(self, limit: int = 50, offset: int = 0) -> APIResponse:
        """List all posts."""
        return self._request('GET', 'posts', params={'limit': limit, 'offset': offset})
    
    def create_post(self, title: str, slug: str, content: str,
                    status: str = 'draft', format: str = 'markdown',
                    **kwargs) -> APIResponse:
        """Create a new post."""
        data = {
            'title': title,
            'slug': slug,
            'content': content,
            'status': status,
            'format': format,
            **kwargs
        }
        return self._request('POST', 'posts', data=data)
    
    def get_post(self, post_id: str) -> APIResponse:
        """Get post by ID."""
        return self._request('GET', f'posts/{post_id}')
    
    def update_post(self, post_id: str, **kwargs) -> APIResponse:
        """Update post."""
        return self._request('PUT', f'posts/{post_id}', data=kwargs)
    
    def delete_post(self, post_id: str) -> APIResponse:
        """Delete post."""
        return self._request('DELETE', f'posts/{post_id}')
    
    # ==================== Media ====================
    
    def list_media(self, limit: int = 50) -> APIResponse:
        """List all media files."""
        return self._request('GET', 'media', params={'limit': limit})
    
    def upload_media(self, file_path: str, **kwargs) -> APIResponse:
        """
        Upload media file.
        
        Args:
            file_path: Path to file to upload
            **kwargs: Additional metadata
        
        Returns:
            APIResponse with uploaded file data
        """
        import os
        
        url = urljoin(f"{self.base_url}/", "api/v1/admin/media")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                data = kwargs
                
                # Remove Content-Type for multipart
                headers = dict(self._session.headers)
                del headers['Content-Type']
                
                response = self._session.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = response.text
                
                success = 200 <= response.status_code < 300
                
                return APIResponse(
                    success=success,
                    data=response_data,
                    status_code=response.status_code,
                    error=None if success else response_data.get('error', 'Unknown error')
                )
                
        except Exception as e:
            return APIResponse(False, None, 0, str(e))
    
    def delete_media(self, media_id: str) -> APIResponse:
        """Delete media file."""
        return self._request('DELETE', f'media/{media_id}')
    
    # ==================== Settings ====================
    
    def get_settings(self) -> APIResponse:
        """Get all settings."""
        return self._request('GET', 'settings')
    
    def update_settings(self, **settings) -> APIResponse:
        """Update settings."""
        return self._request('PUT', 'settings', data=settings)
    
    # ==================== Cache ====================
    
    def get_cache_stats(self) -> APIResponse:
        """Get cache statistics."""
        return self._request('GET', 'cache/stats')
    
    def clear_cache(self, pattern: str = '*') -> APIResponse:
        """Clear cache."""
        return self._request('POST', 'cache/invalidate', data={'pattern': pattern})
    
    def warm_cache(self) -> APIResponse:
        """Warm cache."""
        return self._request('POST', 'cache/warm')
    
    # ==================== Backups ====================
    
    def list_backups(self) -> APIResponse:
        """List all backups."""
        return self._request('GET', 'backups')
    
    def create_backup(self, name: Optional[str] = None) -> APIResponse:
        """Create new backup."""
        data = {'name': name} if name else None
        return self._request('POST', 'backups', data=data)
    
    def restore_backup(self, backup_id: str) -> APIResponse:
        """Restore from backup."""
        return self._request('POST', f'backups/{backup_id}/restore')
    
    def delete_backup(self, backup_id: str) -> APIResponse:
        """Delete backup."""
        return self._request('DELETE', f'backups/{backup_id}')
    
    # ==================== Webhooks ====================
    
    def list_webhooks(self) -> APIResponse:
        """List all webhooks."""
        return self._request('GET', 'webhooks')
    
    def create_webhook(self, url: str, events: List[str],
                       secret: Optional[str] = None) -> APIResponse:
        """Create webhook."""
        data = {'url': url, 'events': events}
        if secret:
            data['secret'] = secret
        return self._request('POST', 'webhooks', data=data)
    
    def delete_webhook(self, webhook_id: str) -> APIResponse:
        """Delete webhook."""
        return self._request('DELETE', f'webhooks/{webhook_id}')
    
    # ==================== Tasks ====================
    
    def list_tasks(self) -> APIResponse:
        """List scheduled tasks."""
        return self._request('GET', 'tasks')
    
    def run_task(self, task_id: str) -> APIResponse:
        """Run task manually."""
        return self._request('POST', f'tasks/{task_id}/run')
    
    # ==================== System ====================
    
    def get_health(self) -> APIResponse:
        """Get system health."""
        # Health endpoint might be public
        url = urljoin(f"{self.base_url}/", "health")
        try:
            response = self._session.get(url, timeout=10)
            return APIResponse(
                success=response.status_code == 200,
                data=response.json() if response.content else None,
                status_code=response.status_code
            )
        except Exception as e:
            return APIResponse(False, None, 0, str(e))
    
    def get_system_stats(self) -> APIResponse:
        """Get system statistics."""
        return self._request('GET', 'system/stats')
    
    # ==================== Import/Export ====================
    
    def export_data(self, entity_type: str, format: str = 'json') -> APIResponse:
        """
        Export data.
        
        Args:
            entity_type: Type of entity (users, content, etc.)
            format: Export format (json, csv, xml)
        
        Returns:
            APIResponse with exported data or download URL
        """
        return self._request(
            'GET',
            f'export/{entity_type}',
            params={'format': format}
        )
    
    def import_data(self, entity_type: str, file_path: str,
                    format: str = 'json') -> APIResponse:
        """
        Import data from file.
        
        Args:
            entity_type: Type of entity
            file_path: Path to import file
            format: File format
        
        Returns:
            APIResponse with import results
        """
        url = urljoin(
            f"{self.base_url}/",
            f"api/v1/admin/import/{entity_type}"
        )
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {'format': format}
                
                headers = dict(self._session.headers)
                del headers['Content-Type']
                
                response = self._session.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=120
                )
                
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    response_data = response.text
                
                return APIResponse(
                    success=200 <= response.status_code < 300,
                    data=response_data,
                    status_code=response.status_code,
                    error=None if response.ok else str(response_data)
                )
                
        except Exception as e:
            return APIResponse(False, None, 0, str(e))


# Convenience function for quick client creation
def create_client(base_url: str, **kwargs) -> WebCMSAdminClient:
    """
    Create WebCMS Admin client.
    
    Args:
        base_url: Base URL of WebCMS instance
        **kwargs: Authentication credentials (api_key or username/password)
    
    Returns:
        WebCMSAdminClient instance
    
    Example:
        client = create_client('https://example.com', username='admin', password='secret')
        users = client.list_users()
    """
    return WebCMSAdminClient(base_url, **kwargs)


# Export
__all__ = [
    'WebCMSAdminClient',
    'APIResponse',
    'create_client'
]
