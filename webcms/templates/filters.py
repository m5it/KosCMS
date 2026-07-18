"""
Template Filters Registration

Custom Jinja2 filters for WebCMS.
"""

import re
from datetime import datetime
from typing import Any

try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    markdown = None


def register_filters(env):
    """
    Register all custom filters with Jinja2 environment.
    
    Args:
        env: Jinja2 Environment
    """
    
    @env.filter('date_format')
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
    
    @env.filter('time_ago')
    def time_ago(value):
        """Format as relative time."""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        
        if not isinstance(value, datetime):
            return value
        
        now = datetime.utcnow()
        diff = now - value
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return value.strftime('%Y-%m-%d')
    
    @env.filter('markdown')
    def markdown_filter(text):
        """Convert markdown to HTML."""
        if not text:
            return ""
        if MARKDOWN_AVAILABLE and markdown:
            try:
                md = markdown.Markdown(extensions=[
                    'fenced_code',
                    'tables',
                    'toc',
                    'nl2br'
                ])
                return md.convert(text)
            except Exception:
                pass
        # Fallback: return text with line breaks converted to <br>
        return str(text).replace('\n', '<br>\n')
    
    @env.filter('truncate')
    def truncate_filter(text, length=100, suffix='...'):
        """Truncate text to length."""
        if not text:
            return ""
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + suffix
    
    @env.filter('strip_tags')
    def strip_tags(text):
        """Remove HTML tags."""
        if not text:
            return ""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    @env.filter('slugify')
    def slugify(text):
        """Convert to URL slug."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text.strip('-')
    
    @env.filter('filesize')
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
    
    @env.filter('pluralize')
    def pluralize(count, singular='', plural='s'):
        """Pluralize word based on count."""
        return singular if count == 1 else plural
    
    @env.filter('highlight')
    def highlight(text, search):
        """Highlight search term in text."""
        if not search:
            return text
        pattern = re.compile(re.escape(search), re.IGNORECASE)
        return pattern.sub(f'<mark>{search}</mark>', text)
