"""
API Documentation Generator

Automatically generates documentation from API code
"""

import inspect
import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class APIEndpointDoc:
    """API endpoint documentation."""
    path: str
    method: str
    description: str
    parameters: List[Dict]
    request_body: Optional[Dict]
    responses: List[Dict]
    auth_required: bool
    rate_limited: bool


class APIDocGenerator:
    """Generate API documentation."""
    
    def __init__(self, title: str = 'WebCMS Admin API', version: str = '1.0.0'):
        self.title = title
        self.version = version
        self.endpoints: List[APIEndpointDoc] = []
    
    def add_endpoint(self, endpoint: APIEndpointDoc):
        """Add endpoint documentation."""
        self.endpoints.append(endpoint)
    
    def generate_openapi(self) -> Dict:
        """Generate OpenAPI/Swagger specification."""
        spec = {
            'openapi': '3.0.0',
            'info': {
                'title': self.title,
                'version': self.version,
                'description': 'WebCMS Admin Panel REST API'
            },
            'servers': [
                {'url': '/api/v1', 'description': 'API v1'}
            ],
            'paths': {},
            'components': {
                'securitySchemes': {
                    'bearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    }
                },
                'schemas': self._generate_schemas()
            }
        }
        
        for endpoint in self.endpoints:
            path = f"/admin{endpoint.path}"
            method = endpoint.method.lower()
            
            if path not in spec['paths']:
                spec['paths'][path] = {}
            
            spec['paths'][path][method] = {
                'summary': endpoint.description,
                'operationId': f"{method}_{endpoint.path.replace('/', '_').strip('_')}",
                'parameters': endpoint.parameters,
                'responses': self._format_responses(endpoint.responses),
                'security': [{'bearerAuth': []}] if endpoint.auth_required else []
            }
            
            if endpoint.request_body:
                spec['paths'][path][method]['requestBody'] = {
                    'required': True,
                    'content': {
                        'application/json': {
                            'schema': endpoint.request_body
                        }
                    }
                }
        
        return spec
    
    def _generate_schemas(self) -> Dict:
        """Generate component schemas."""
        return {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string', 'format': 'email'},
                    'role': {'type': 'string'},
                    'is_active': {'type': 'boolean'},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'Page': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'title': {'type': 'string'},
                    'slug': {'type': 'string'},
                    'content': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['draft', 'published', 'archived']},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'Post': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'title': {'type': 'string'},
                    'slug': {'type': 'string'},
                    'content': {'type': 'string'},
                    'status': {'type': 'string', 'enum': ['draft', 'published', 'archived']},
                    'format': {'type': 'string', 'enum': ['html', 'markdown']},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'Error': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'message': {'type': 'string'}
                }
            }
        }
    
    def _format_responses(self, responses: List[Dict]) -> Dict:
        """Format response definitions."""
        formatted = {}
        for resp in responses:
            code = str(resp.get('code', 200))
            formatted[code] = {
                'description': resp.get('description', 'Success'),
                'content': {
                    'application/json': {
                        'schema': resp.get('schema', {'type': 'object'})
                    }
                }
            }
        return formatted
    
    def generate_markdown(self) -> str:
        """Generate Markdown documentation."""
        lines = [
            f"# {self.title}",
            "",
            f"**Version:** {self.version}",
            "",
            "## Base URL",
            "",
            "```",
            "/api/v1/admin",
            "```",
            "",
            "## Authentication",
            "",
            "All endpoints require authentication via Bearer token:",
            "",
            "```",
            "Authorization: Bearer <your-jwt-token>",
            "```",
            "",
            "---",
            "",
            "## Endpoints",
            ""
        ]
        
        # Group by path
        by_path: Dict[str, List[APIEndpointDoc]] = {}
        for ep in self.endpoints:
            if ep.path not in by_path:
                by_path[ep.path] = []
            by_path[ep.path].append(ep)
        
        for path, endpoints in sorted(by_path.items()):
            lines.append(f"### {path}")
            lines.append("")
            
            for ep in endpoints:
                auth_badge = "🔒" if ep.auth_required else "🌐"
                rate_badge = "⏱️" if ep.rate_limited else ""
                
                lines.append(f"#### {ep.method.upper()} {auth_badge} {rate_badge}")
                lines.append("")
                lines.append(ep.description)
                lines.append("")
                
                if ep.parameters:
                    lines.append("**Parameters:**")
                    lines.append("")
                    lines.append("| Name | Type | Required | Description |")
                    lines.append("|------|------|----------|-------------|")
                    for param in ep.parameters:
                        req = "Yes" if param.get('required') else "No"
                        lines.append(f"| {param.get('name')} | {param.get('type')} | {req} | {param.get('description', '')} |")
                    lines.append("")
                
                if ep.request_body:
                    lines.append("**Request Body:**")
                    lines.append("")
                    lines.append("```json")
                    lines.append(json.dumps(ep.request_body, indent=2))
                    lines.append("```")
                    lines.append("")
                
                if ep.responses:
                    lines.append("**Responses:**")
                    lines.append("")
                    for resp in ep.responses:
                        lines.append(f"- **{resp.get('code')}** - {resp.get('description')}")
                    lines.append("")
                
                lines.append("---")
                lines.append("")
        
        return "\n".join(lines)
    
    def save_openapi(self, filepath: str = 'openapi.json'):
        """Save OpenAPI spec to file."""
        spec = self.generate_openapi()
        with open(filepath, 'w') as f:
            json.dump(spec, f, indent=2)
        print(f"Saved OpenAPI spec to {filepath}")
    
    def save_markdown(self, filepath: str = 'API_REFERENCE.md'):
        """Save Markdown docs to file."""
        docs = self.generate_markdown()
        with open(filepath, 'w') as f:
            f.write(docs)
        print(f"Saved Markdown docs to {filepath}")


def generate_from_admin_api():
    """Generate documentation from AdminAPI class."""
    from webcms.admin.admin_api import AdminAPI
    
    generator = APIDocGenerator()
    
    # Dashboard
    generator.add_endpoint(APIEndpointDoc(
        path='/dashboard',
        method='GET',
        description='Get dashboard statistics and widgets',
        parameters=[],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'Dashboard data', 'schema': {'type': 'object'}}
        ],
        auth_required=True,
        rate_limited=False
    ))
    
    # Users
    generator.add_endpoint(APIEndpointDoc(
        path='/users',
        method='GET',
        description='List all users with pagination',
        parameters=[
            {'name': 'limit', 'type': 'integer', 'required': False, 'description': 'Max results'},
            {'name': 'offset', 'type': 'integer', 'required': False, 'description': 'Skip results'}
        ],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'List of users', 'schema': {'type': 'object'}}
        ],
        auth_required=True,
        rate_limited=True
    ))
    
    generator.add_endpoint(APIEndpointDoc(
        path='/users',
        method='POST',
        description='Create a new user',
        parameters=[],
        request_body={
            'username': 'string',
            'email': 'string',
            'password': 'string',
            'role': 'string'
        },
        responses=[
            {'code': 201, 'description': 'User created'},
            {'code': 400, 'description': 'Invalid data'}
        ],
        auth_required=True,
        rate_limited=True
    ))
    
    # Content
    generator.add_endpoint(APIEndpointDoc(
        path='/pages',
        method='GET',
        description='List all pages',
        parameters=[],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'List of pages'}
        ],
        auth_required=True,
        rate_limited=False
    ))
    
    generator.add_endpoint(APIEndpointDoc(
        path='/posts',
        method='GET',
        description='List all posts',
        parameters=[],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'List of posts'}
        ],
        auth_required=True,
        rate_limited=False
    ))
    
    # Settings
    generator.add_endpoint(APIEndpointDoc(
        path='/settings',
        method='GET',
        description='Get all settings',
        parameters=[],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'Settings object'}
        ],
        auth_required=True,
        rate_limited=False
    ))
    
    generator.add_endpoint(APIEndpointDoc(
        path='/settings',
        method='PUT',
        description='Update settings',
        parameters=[],
        request_body={
            'site_name': 'string',
            'posts_per_page': 'integer'
        },
        responses=[
            {'code': 200, 'description': 'Settings updated'}
        ],
        auth_required=True,
        rate_limited=True
    ))
    
    # Cache
    generator.add_endpoint(APIEndpointDoc(
        path='/cache/stats',
        method='GET',
        description='Get cache statistics',
        parameters=[],
        request_body=None,
        responses=[
            {'code': 200, 'description': 'Cache statistics'}
        ],
        auth_required=True,
        rate_limited=False
    ))
    
    return generator


# Export
__all__ = [
    'APIEndpointDoc',
    'APIDocGenerator',
    'generate_from_admin_api'
]
