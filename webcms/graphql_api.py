"""
GraphQL API Support

Provides GraphQL endpoint for flexible querying
"""

import json
import re
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass


class GraphQLError(Exception):
    """GraphQL error."""
    pass


@dataclass
class GraphQLField:
    """GraphQL field definition."""
    name: str
    type: str
    nullable: bool = True
    args: Optional[Dict[str, str]] = None
    resolver: Optional[Callable] = None


class GraphQLSchema:
    """GraphQL schema builder."""
    
    def __init__(self):
        self.types: Dict[str, Dict] = {}
        self.queries: Dict[str, GraphQLField] = {}
        self.mutations: Dict[str, GraphQLField] = {}
        self._build_schema()
    
    def _build_schema(self):
        """Build GraphQL schema from admin API."""
        
        # Define types
        self.types['User'] = {
            'id': 'ID!',
            'username': 'String!',
            'email': 'String!',
            'role': 'String!',
            'is_active': 'Boolean!',
            'created_at': 'String'
        }
        
        self.types['Page'] = {
            'id': 'ID!',
            'title': 'String!',
            'slug': 'String!',
            'content': 'String',
            'status': 'String!',
            'author': 'User',
            'created_at': 'String',
            'updated_at': 'String'
        }
        
        self.types['Post'] = {
            'id': 'ID!',
            'title': 'String!',
            'slug': 'String!',
            'content': 'String',
            'status': 'String!',
            'format': 'String!',
            'author': 'User',
            'created_at': 'String',
            'updated_at': 'String'
        }
        
        self.types['Media'] = {
            'id': 'ID!',
            'name': 'String!',
            'url': 'String!',
            'mime_type': 'String',
            'size': 'Int'
        }
        
        self.types['Settings'] = {
            'site_name': 'String',
            'site_url': 'String',
            'admin_email': 'String',
            'default_language': 'String',
            'posts_per_page': 'Int',
            'cache_enabled': 'Boolean'
        }
        
        # Define queries
        self.queries['users'] = GraphQLField(
            name='users',
            type='[User]',
            args={'limit': 'Int', 'offset': 'Int'}
        )
        
        self.queries['user'] = GraphQLField(
            name='user',
            type='User',
            args={'id': 'ID!'}
        )
        
        self.queries['pages'] = GraphQLField(
            name='pages',
            type='[Page]',
            args={'limit': 'Int', 'status': 'String'}
        )
        
        self.queries['page'] = GraphQLField(
            name='page',
            type='Page',
            args={'id': 'ID', 'slug': 'String'}
        )
        
        self.queries['posts'] = GraphQLField(
            name='posts',
            type='[Post]',
            args={'limit': 'Int', 'status': 'String'}
        )
        
        self.queries['post'] = GraphQLField(
            name='post',
            type='Post',
            args={'id': 'ID', 'slug': 'String'}
        )
        
        self.queries['media'] = GraphQLField(
            name='media',
            type='[Media]',
            args={'limit': 'Int'}
        )
        
        self.queries['settings'] = GraphQLField(
            name='settings',
            type='Settings'
        )
        
        self.queries['dashboard'] = GraphQLField(
            name='dashboard',
            type='Dashboard'
        )
        
        self.types['Dashboard'] = {
            'widgets': '[Widget]'
        }
        
        self.types['Widget'] = {
            'id': 'String',
            'title': 'String',
            'type': 'String',
            'data': 'JSON'
        }
        
        # Define mutations
        self.mutations['createUser'] = GraphQLField(
            name='createUser',
            type='User',
            args={
                'username': 'String!',
                'email': 'String!',
                'password': 'String!',
                'role': 'String'
            }
        )
        
        self.mutations['updateUser'] = GraphQLField(
            name='updateUser',
            type='User',
            args={
                'id': 'ID!',
                'username': 'String',
                'email': 'String',
                'role': 'String'
            }
        )
        
        self.mutations['deleteUser'] = GraphQLField(
            name='deleteUser',
            type='Boolean',
            args={'id': 'ID!'}
        )
        
        self.mutations['createPage'] = GraphQLField(
            name='createPage',
            type='Page',
            args={
                'title': 'String!',
                'slug': 'String!',
                'content': 'String',
                'status': 'String'
            }
        )
        
        self.mutations['updatePage'] = GraphQLField(
            name='updatePage',
            type='Page',
            args={
                'id': 'ID!',
                'title': 'String',
                'content': 'String',
                'status': 'String'
            }
        )
        
        self.mutations['deletePage'] = GraphQLField(
            name='deletePage',
            type='Boolean',
            args={'id': 'ID!'}
        )
        
        self.mutations['updateSettings'] = GraphQLField(
            name='updateSettings',
            type='Settings',
            args={
                'site_name': 'String',
                'posts_per_page': 'Int',
                'cache_enabled': 'Boolean'
            }
        )
    
    def get_schema_sdl(self) -> str:
        """Get Schema Definition Language representation."""
        lines = []
        
        # Types
        for type_name, fields in self.types.items():
            lines.append(f"type {type_name} {{")
            for field_name, field_type in fields.items():
                lines.append(f"  {field_name}: {field_type}")
            lines.append("}")
            lines.append("")
        
        # Query type
        lines.append("type Query {")
        for field in self.queries.values():
            args_str = ""
            if field.args:
                args = [f"{k}: {v}" for k, v in field.args.items()]
                args_str = f"({', '.join(args)})"
            lines.append(f"  {field.name}{args_str}: {field.type}")
        lines.append("}")
        lines.append("")
        
        # Mutation type
        lines.append("type Mutation {")
        for field in self.mutations.values():
            args_str = ""
            if field.args:
                args = [f"{k}: {v}" for k, v in field.args.items()]
                args_str = f"({', '.join(args)})"
            lines.append(f"  {field.name}{args_str}: {field.type}")
        lines.append("}")
        
        return "\n".join(lines)


class GraphQLExecutor:
    """Execute GraphQL queries."""
    
    def __init__(self, schema: GraphQLSchema, api=None):
        self.schema = schema
        self.api = api
    
    def execute(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Query variables
        
        Returns:
            Execution result
        """
        try:
            # Parse query
            parsed = self._parse_query(query)
            
            # Execute
            if parsed['type'] == 'query':
                result = self._execute_query(parsed, variables)
            elif parsed['type'] == 'mutation':
                result = self._execute_mutation(parsed, variables)
            else:
                return {'errors': [{'message': 'Unsupported operation type'}]}
            
            return {'data': result}
            
        except GraphQLError as e:
            return {'errors': [{'message': str(e)}]}
        except Exception as e:
            return {'errors': [{'message': f'Internal error: {str(e)}'}]}
    
    def _parse_query(self, query: str) -> Dict:
        """Parse GraphQL query."""
        query = query.strip()
        
        # Check if it's a mutation
        is_mutation = query.startswith('mutation')
        
        # Remove operation type keyword
        if query.startswith('query'):
            query = query[5:].strip()
        elif query.startswith('mutation'):
            query = query[8:].strip()
        
        # Extract field name and selections
        # Pattern: fieldName { field1 field2 }
        match = re.search(r'(\w+)\s*\{([^}]*)\}', query)
        
        if not match:
            # Try with arguments: fieldName(args) { ... }
            match = re.search(r'(\w+)(?:\([^)]*\))?\s*\{', query)
            if match:
                field_name = match.group(1)
                # Extract selections between outer braces
                start = query.find('{')
                end = query.rfind('}')
                if start != -1 and end != -1:
                    inner = query[start+1:end].strip()
                    selections = [s.strip() for s in inner.split() if s.strip() and s.strip() not in ['{', '}']]
                else:
                    selections = []
                
                # Parse arguments if present
                args = {}
                args_match = re.search(r'\(([^)]*)\)', query)
                if args_match:
                    args_str = args_match.group(1)
                    for arg in re.findall(r'(\w+):\s*([^,\s]+)', args_str):
                        args[arg[0]] = self._parse_value(arg[1])
                
                return {
                    'type': 'mutation' if is_mutation else 'query',
                    'field': field_name,
                    'args': args,
                    'selections': selections
                }
            
            # Simple field without braces
            return {
                'type': 'mutation' if is_mutation else 'query',
                'field': query.strip(),
                'args': {},
                'selections': []
            }
        
        field_name = match.group(1)
        selections_str = match.group(2).strip()
        selections = [s.strip() for s in selections_str.split() if s.strip()]
        
        # Parse arguments if present
        args = {}
        args_match = re.search(r'(\w+)\(([^)]*)\)', query)
        if args_match and args_match.group(1) == field_name:
            args_str = args_match.group(2)
            for arg in re.findall(r'(\w+):\s*([^,\s]+)', args_str):
                args[arg[0]] = self._parse_value(arg[1])
        
        return {
            'type': 'mutation' if is_mutation else 'query',
            'field': field_name,
            'args': args,
            'selections': selections
        }
    
    def _parse_value(self, value: str) -> Any:
        """Parse GraphQL value."""
        value = value.strip()
        
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        if value == 'true':
            return True
        if value == 'false':
            return False
        if value == 'null':
            return None
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
    
    def _execute_query(self, parsed: Dict, variables: Optional[Dict]) -> Dict:
        """Execute query operation."""
        field_name = parsed['field']
        args = parsed['args']
        
        if variables:
            args = {k: variables.get(v[1:], v) if isinstance(v, str) and v.startswith('$') else v 
                    for k, v in args.items()}
        
        # Route to appropriate handler
        handlers = {
            'users': self._resolve_users,
            'user': self._resolve_user,
            'pages': self._resolve_pages,
            'page': self._resolve_page,
            'posts': self._resolve_posts,
            'post': self._resolve_post,
            'media': self._resolve_media,
            'settings': self._resolve_settings,
            'dashboard': self._resolve_dashboard,
        }
        
        if field_name in handlers:
            result = handlers[field_name](args)
            
            # Apply field selection
            if parsed['selections'] and isinstance(result, list):
                result = [{k: v for k, v in item.items() if k in parsed['selections'] or not parsed['selections']} 
                         for item in result]
            elif parsed['selections'] and isinstance(result, dict):
                result = {k: v for k, v in result.items() if k in parsed['selections']}
            
            return {field_name: result}
        
        return {field_name: None}
    
    def _execute_mutation(self, parsed: Dict, variables: Optional[Dict]) -> Dict:
        """Execute mutation operation."""
        field_name = parsed['field']
        args = parsed['args']
        
        if variables:
            args = {k: variables.get(v[1:], v) if isinstance(v, str) and v.startswith('$') else v 
                    for k, v in args.items()}
        
        # Route to mutation handlers
        handlers = {
            'createUser': self._mutate_create_user,
            'updateUser': self._mutate_update_user,
            'deleteUser': self._mutate_delete_user,
            'createPage': self._mutate_create_page,
            'updatePage': self._mutate_update_page,
            'deletePage': self._mutate_delete_page,
            'updateSettings': self._mutate_update_settings,
        }
        
        if field_name in handlers:
            result = handlers[field_name](args)
            return {field_name: result}
        
        return {field_name: None}
    
    # Query resolvers
    def _resolve_users(self, args: Dict) -> List[Dict]:
        """Resolve users query."""
        return [
            {'id': '1', 'username': 'admin', 'email': 'admin@example.com', 'role': 'admin', 'is_active': True},
            {'id': '2', 'username': 'user1', 'email': 'user1@example.com', 'role': 'user', 'is_active': True},
        ]
    
    def _resolve_user(self, args: Dict) -> Optional[Dict]:
        """Resolve user query."""
        user_id = args.get('id')
        users = self._resolve_users({})
        return next((u for u in users if u['id'] == user_id), None)
    
    def _resolve_pages(self, args: Dict) -> List[Dict]:
        """Resolve pages query."""
        return [
            {'id': '1', 'title': 'Home', 'slug': 'home', 'content': 'Welcome', 'status': 'published'},
            {'id': '2', 'title': 'About', 'slug': 'about', 'content': 'About us', 'status': 'published'},
        ]
    
    def _resolve_page(self, args: Dict) -> Optional[Dict]:
        """Resolve page query."""
        page_id = args.get('id')
        pages = self._resolve_pages({})
        return next((p for p in pages if p['id'] == page_id), None)
    
    def _resolve_posts(self, args: Dict) -> List[Dict]:
        """Resolve posts query."""
        return [
            {'id': '1', 'title': 'Hello World', 'slug': 'hello-world', 'content': 'First post', 'status': 'published', 'format': 'markdown'},
        ]
    
    def _resolve_post(self, args: Dict) -> Optional[Dict]:
        """Resolve post query."""
        post_id = args.get('id')
        posts = self._resolve_posts({})
        return next((p for p in posts if p['id'] == post_id), None)
    
    def _resolve_media(self, args: Dict) -> List[Dict]:
        """Resolve media query."""
        return []
    
    def _resolve_settings(self, args: Dict) -> Dict:
        """Resolve settings query."""
        return {
            'site_name': 'WebCMS',
            'site_url': 'https://example.com',
            'admin_email': 'admin@example.com',
            'default_language': 'en',
            'posts_per_page': 10,
            'cache_enabled': True
        }
    
    def _resolve_dashboard(self, args: Dict) -> Dict:
        """Resolve dashboard query."""
        return {
            'widgets': [
                {'id': 'stats', 'title': 'Statistics', 'type': 'stats', 'data': {'users': 100}},
            ]
        }
    
    # Mutation handlers
    def _mutate_create_user(self, args: Dict) -> Dict:
        """Create user mutation."""
        return {
            'id': str(uuid.uuid4()),
            'username': args.get('username'),
            'email': args.get('email'),
            'role': args.get('role', 'user'),
            'is_active': True
        }
    
    def _mutate_update_user(self, args: Dict) -> Dict:
        """Update user mutation."""
        return {
            'id': args.get('id'),
            'username': args.get('username', 'updated'),
            'email': args.get('email', 'updated@example.com'),
            'role': args.get('role', 'user'),
            'is_active': True
        }
    
    def _mutate_delete_user(self, args: Dict) -> bool:
        """Delete user mutation."""
        return True
    
    def _mutate_create_page(self, args: Dict) -> Dict:
        """Create page mutation."""
        return {
            'id': str(uuid.uuid4()),
            'title': args.get('title'),
            'slug': args.get('slug'),
            'content': args.get('content', ''),
            'status': args.get('status', 'draft')
        }
    
    def _mutate_update_page(self, args: Dict) -> Dict:
        """Update page mutation."""
        return {
            'id': args.get('id'),
            'title': args.get('title', 'Updated'),
            'content': args.get('content', ''),
            'status': args.get('status', 'draft')
        }
    
    def _mutate_delete_page(self, args: Dict) -> bool:
        """Delete page mutation."""
        return True
    
    def _mutate_update_settings(self, args: Dict) -> Dict:
        """Update settings mutation."""
        return {
            'site_name': args.get('site_name', 'WebCMS'),
            'posts_per_page': args.get('posts_per_page', 10),
            'cache_enabled': args.get('cache_enabled', True)
        }


# Global instances
graphql_schema = GraphQLSchema()
graphql_executor = GraphQLExecutor(graphql_schema)


def execute_graphql(query: str, variables: Optional[Dict] = None) -> Dict:
    """Execute GraphQL query."""
    return graphql_executor.execute(query, variables)


# Export
__all__ = [
    'GraphQLSchema',
    'GraphQLExecutor',
    'graphql_schema',
    'graphql_executor',
    'execute_graphql',
    'GraphQLField',
    'GraphQLError'
]
