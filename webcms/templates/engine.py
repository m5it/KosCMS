"""
Template Engine

Jinja2 integration with custom filters and caching.
"""

import logging
import os
import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger("webcms.templates.engine")

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = None
    FileSystemLoader = None
    select_autoescape = None


class TemplateEngine:
    """Jinja2 template engine wrapper."""
    
    def __init__(self, template_dirs: List[str] = None, 
                 cache_enabled: bool = True,
                 redis_client=None,
                 db=None):
        self.template_dirs = template_dirs or []
        self.cache_enabled = cache_enabled
        self.redis = redis_client
        self.db = db
        
        # Create Jinja2 environment if available
        self.env = None
        if JINJA2_AVAILABLE and self.template_dirs:
            try:
                self.env = Environment(
                    loader=FileSystemLoader(self.template_dirs),
                    autoescape=select_autoescape(['html', 'xml']),
                    trim_blocks=True,
                    lstrip_blocks=True
                )
                self._register_filters()
            except Exception:
                pass
        
        # Template cache
        self._cache: Dict[str, str] = {}
    
    @staticmethod
    def _sql_escape(value) -> str:
        """Escape a value for use in a KosDB SQL string."""
        if value is None:
            return "NULL"
        return str(value).replace("'", "''")
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        cls = getattr(self.db, '__class__', type(self.db))
        cls_name = getattr(cls, '__name__', '')
        return 'KosDB' in cls_name
    
    def _register_filters(self) -> None:
        """Register custom template filters."""
        if not self.env:
            return
        
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
            if MARKDOWN_AVAILABLE and markdown:
                try:
                    md = markdown.Markdown(extensions=[
                        'fenced_code',
                        'tables',
                        'toc'
                    ])
                    return md.convert(text)
                except Exception:
                    pass
            # Fallback: return text as-is
            return str(text)
        
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
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[-\s]+', '-', text)
            return text.strip('-')
        
        @self.env.filter('filesize')
        def filesize_filter(size):
            """Format file size."""
            try:
                size = float(size)
            except (ValueError, TypeError):
                return str(size)
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
        if not self.env:
            return f""
        
        context = context or {}
        
        # Check cache
        cache_key = f"template:{template_name}:{hash(str(context))}"
        if self.cache_enabled:
            cached = self._get_cache(cache_key)
            if cached:
                return cached
        
        # Render template
        try:
            template = self.env.get_template(template_name)
            html = template.render(**context)
        except Exception:
            return f""
        
        # Store in cache
        if self.cache_enabled:
            self._set_cache(cache_key, html)
        
        return html
    
    def render_string(self, source: str, context: Dict[str, Any] = None) -> str:
        """Render template from string."""
        if not JINJA2_AVAILABLE:
            return f""
        from jinja2 import Template
        template = Template(source)
        return template.render(**(context or {}))
    
    def _get_cache(self, key: str) -> Optional[str]:
        """Get cached template."""
        if self.redis:
            try:
                data = self.redis.get(key)
                return data.decode() if data else None
            except Exception:
                pass
        return self._cache.get(key)
    
    def _set_cache(self, key: str, value: str, timeout: int = 300) -> None:
        """Cache rendered template."""
        if self.redis:
            try:
                self.redis.setex(key, timeout, value)
            except Exception:
                pass
        else:
            self._cache[key] = value
    
    def clear_cache(self) -> None:
        """Clear template cache."""
        if self.redis:
            # Delete template keys
            try:
                for key in self.redis.scan_iter("template:*"):
                    self.redis.delete(key)
            except Exception:
                pass
        self._cache.clear()
    
    def _discover_templates_from_disk(self) -> List[Dict[str, Any]]:
        """Discover templates from filesystem."""
        templates = []
        
        # Look in template directories
        for template_dir in self.template_dirs:
            if not os.path.exists(template_dir):
                continue
            
            try:
                for root, dirs, files in os.walk(template_dir):
                    for file in files:
                        if file.endswith(('.html', '.j2', '.jinja')):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, template_dir)
                            name = rel_path.replace(os.sep, '/')
                            template_id = name.replace('/', '_').replace('.', '_')
                            
                            templates.append({
                                "id": template_id,
                                "name": name,
                                "path": rel_path,
                                "updated_at": datetime.utcnow().isoformat()
                            })
            except Exception:
                pass
        
        return templates
    
    def _ensure_templates_table_kosdb(self):
        """Ensure templates table exists in KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
            if 'templates' in tables:
                return
        except Exception:
            pass
        
        try:
            self.db.execute(
                "CREATE TABLE templates ("
                "id TEXT PRIMARY KEY, "
                "name TEXT, "
                "path TEXT, "
                "content TEXT, "
                "updated_at TEXT, "
                "is_active TEXT DEFAULT '1'"
                ")"
            )
        except Exception:
            pass
    
    def _sync_templates_to_kosdb(self, templates: List[Dict[str, Any]]):
        """Sync discovered templates to KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        self._ensure_templates_table_kosdb()
        
        # Get existing templates
        try:
            result = self.db.query("SELECT id FROM templates WHERE is_active='1'")
            existing_ids = {row.get('id') for row in result.get('rows', [])}
        except Exception as e:
            logger.warning("Could not list existing templates for sync: %s", e)
            existing_ids = set()
        
        # Insert new templates
        for t in templates:
            if t['id'] not in existing_ids:
                try:
                    self.db.execute(
                        f"INSERT INTO templates (id, name, path, updated_at, is_active) "
                        f"VALUES ('{self._sql_escape(t['id'])}', '{self._sql_escape(t['name'])}', "
                        f"'{self._sql_escape(t['path'])}', '{self._sql_escape(t['updated_at'])}', '1')"
                    )
                except Exception as e:
                    logger.warning("Could not sync template %s to KosDB: %s", t.get('id'), e)
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        Get list of available templates.
        Returns templates from filesystem merged with any KosDB-only templates.
        """
        # Discover from disk (may be empty if no template_dirs exist)
        templates = self._discover_templates_from_disk()
        
        # Sync to KosDB if available
        if self.db and self._is_kosdb():
            self._sync_templates_to_kosdb(templates)
            
            # Merge with DB templates, including DB-only templates
            try:
                result = self.db.query(
                    "SELECT id, name, path, content, updated_at FROM templates WHERE is_active='1'"
                )
                if not result.get('error'):
                    db_templates = {
                        row.get('id'): {
                            "id": row.get('id'),
                            "name": row.get('name'),
                            "path": row.get('path'),
                            "content": row.get('content'),
                            "updated_at": row.get('updated_at', datetime.utcnow().isoformat())
                        }
                        for row in result.get('rows', [])
                    }
                    
                    # Disk templates take precedence for shared fields, but preserve content from DB
                    for t in templates:
                        existing = db_templates.get(t['id'], {})
                        t['content'] = existing.get('content')
                        db_templates[t['id']] = t
                    
                    templates = list(db_templates.values())
            except Exception as e:
                logger.warning("Could not list templates from KosDB: %s", e)
        
        return sorted(templates, key=lambda x: x['name'])
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID, preferring KosDB content."""
        if self.db and self._is_kosdb():
            self._ensure_templates_table_kosdb()
            try:
                result = self.db.query(
                    f"SELECT id, name, path, content, updated_at FROM templates "
                    f"WHERE id='{self._sql_escape(template_id)}' AND is_active='1'"
                )
                if not result.get('error'):
                    rows = result.get('rows', [])
                    if rows:
                        row = rows[0]
                        return {
                            "id": row.get('id'),
                            "name": row.get('name'),
                            "path": row.get('path'),
                            "content": row.get('content'),
                            "updated_at": row.get('updated_at', datetime.utcnow().isoformat())
                        }
            except Exception as e:
                logger.warning("Could not get template %s from KosDB: %s", template_id, e)
        
        templates = self.list_templates()
        for t in templates:
            if t['id'] == template_id:
                return t
        return None
    
    def save_template(self, template_id: str, content: str, name: str = None) -> Dict[str, Any]:
        """Save template content, returning the full saved record."""
        safe_id = re.sub(r"[^a-zA-Z0-9_\-/]", "", template_id).strip("/")
        if not safe_id:
            return {"id": template_id, "error": "Invalid template id"}
        
        template_name = name or safe_id.replace('_', '/')
        template_path = template_name
        now = datetime.utcnow().isoformat()
        
        if self.db and self._is_kosdb():
            self._ensure_templates_table_kosdb()
            try:
                result = self.db.query(
                    f"SELECT id FROM templates WHERE id='{self._sql_escape(safe_id)}'"
                )
                if result.get('rows'):
                    self.db.execute(
                        f"UPDATE templates SET "
                        f"name='{self._sql_escape(template_name)}', "
                        f"path='{self._sql_escape(template_path)}', "
                        f"content='{self._sql_escape(content)}', "
                        f"updated_at='{self._sql_escape(now)}' "
                        f"WHERE id='{self._sql_escape(safe_id)}'"
                    )
                else:
                    self.db.execute(
                        f"INSERT INTO templates (id, name, path, content, updated_at, is_active) "
                        f"VALUES ('{self._sql_escape(safe_id)}', '{self._sql_escape(template_name)}', "
                        f"'{self._sql_escape(template_path)}', '{self._sql_escape(content)}', "
                        f"'{self._sql_escape(now)}', '1')"
                    )
                
                return {
                    "id": safe_id,
                    "name": template_name,
                    "path": template_path,
                    "content": content,
                    "updated_at": now
                }
            except Exception as e:
                logger.warning("Could not save template %s to KosDB: %s", safe_id, e)
        
        # Fallback: save to file if we have a template dir
        if self.template_dirs:
            for template_dir in self.template_dirs:
                file_path = os.path.join(template_dir, safe_id.replace('_', '/'))
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, 'w') as f:
                        f.write(content)
                    return {
                        "id": safe_id,
                        "name": template_name,
                        "path": template_path,
                        "content": content,
                        "updated_at": now
                    }
                except Exception as e:
                    logger.warning("Could not save template %s to disk: %s", safe_id, e)
        
        return {"id": template_id, "error": "Could not save template"}
    
    def delete_template(self, template_id: str) -> bool:
        safe_id = re.sub(r"[^a-zA-Z0-9_\-/]", "", template_id).strip("/")
        if not safe_id:
            return False
        if not safe_id:
            return False
        
        if self.db and self._is_kosdb():
            self._ensure_templates_table_kosdb()
            try:
                self.db.execute(
                    f"DELETE FROM templates WHERE id='{self._sql_escape(safe_id)}'"
                )
                return True
            except Exception as e:
                logger.warning("Could not delete template %s from KosDB: %s", safe_id, e)
        
        # Also try to delete from disk
        if self.template_dirs:
            for template_dir in self.template_dirs:
                file_path = os.path.join(template_dir, safe_id.replace('_', '/'))
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        return True
                except Exception as e:
                    logger.warning("Could not delete template %s from disk: %s", safe_id, e)
        
        return False
