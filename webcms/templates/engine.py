"""
Template Engine

Jinja2 integration with custom filters and caching.
"""

import os
import re
import markdown
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateEngine:
    """Jinja2 template engine wrapper."""
    
    def __init__(self, template_dirs: List[str], 
                 cache_enabled: bool = True,
                 redis_client=None):
        self.template_dirs = template_dirs
        self.cache_enabled = cache_enabled
        self.redis = redis_client
        
        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dirs),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_filters()
        
        # Template cache
        self._cache: Dict[str, str] = {}
    
    def _register_filters(self) -> None:
        """Register custom template filters."""
        
        @self.env.filter('date_format')
        def date_format(value, format_str='%Y-%m-%d'):
            """Format date/datetime."""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            if isinstance(value, datetime):
                return value.strftime(format_str)
            return value
        
        @self.env.filter('markdown')
        def markdown_filter(text):
            """Convert markdown to HTML."""
            if not text:
                return ""
            md = markdown.Markdown(extensions=[
                'fenced_code',
                'tables',
                'toc'
            ])
            return md.convert(text)
        
        @self.env.filter('truncate')
        def truncate_filter(text, length=100, suffix='...'):
            """Truncate text to length."""
            if not text:
                return ""
            if len(text) <= length:
                return text
            return text[:length].rsplit(' ', 1)[0] + suffix
        
        @self.env.filter('strip_tags')
        def strip_tags(text):
            """Remove HTML tags."""
            if not text:
                return ""
            clean = re.compile('<.*?>')
            return re.sub(clean, '', text)
        
        @self.env.filter('slugify')
        def slugify(text):
            """Convert to URL slug."""
            if not text:
                return ""
            text = text.lower()
            text = re.sub(r'[^\\w\\s-]', '', text)
            text = re.sub(r'[-\\s]+', '-', text)
            return text.strip('-')
        
        @self.env.filter('filesize')
        def filesize_filter(size):
            """Format file size."""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} TB"
    
    def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        Render template with context.
        
        Args:
            template_name: Template file path
            context: Template variables
        
        Returns:
            Rendered HTML
        """
        context = context or {}
        
        # Check cache
        cache_key = f"template:{template_name}:{hash(str(context))}"
        if self.cache_enabled:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        
        # Render template
        template = self.env.get_template(template_name)
        html = template.render(**context)
        
        # Store in cache
        if self.cache_enabled:
            self._set_cache(cache_key, html)
        
        return html
    
    def render_string(self, source: str, context: Dict[str, Any] = None) -> str:
        """Render template from string."""
        from jinja2 import Template
        template = Template(source)
        return template.render(**(context or {}))
    
    def _get_cache(self, key: str) -> Optional[str]:
        """Get cached template."""
        if self.redis:
            data = self.redis.get(key)
            return data.decode() if data else None
        return self._cache.get(key)
    
    def _set_cache(self, key: str, value: str, timeout: int = 300) -> None:
        """Cache rendered template."""
        if self.redis:
            self.redis.setex(key, timeout, value)
        else:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear template cache."""
        if self.redis:
            # Delete template keys
            for key in self.redis.scan_iter("template:*"):
                self.redis.delete(key)
        self._cache.clear()
    
    def get_template_list(self) -> List[str]:
        """Get list of available templates."""
        templates = []
        for loader in self.env.loader.list_templates():
            templates.append(loader)
        return templates