"""
XSS Filter

Input sanitization and output encoding.
"""

import re
import html
from typing import Optional


class XSSFilter:
    """XSS protection filters."""
    
    # Allowed HTML tags for rich content
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3',
        'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'img', 'blockquote',
        'code', 'pre', 'table', 'thead', 'tbody', 'tr', 'td', 'th'
    }
    
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['class'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan']
    }
    
    # Dangerous patterns
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
        r'expression\s*\(',
    ]
    
    def sanitize_html(self, content: str) -> str:
        """
        Sanitize HTML content.
        
        Removes dangerous tags and attributes while
        preserving allowed formatting.
        
        Args:
            content: Raw HTML content
        
        Returns:
            Sanitized HTML
        """
        if not content:
            return ""
        
        # Remove dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)
        
        # Parse and filter tags
        return self._filter_tags(content)
    
    def _filter_tags(self, html_content: str) -> str:
        """Filter HTML tags."""
        # Simple tag filtering using regex
        def tag_replacer(match):
            tag = match.group(1).lower()
            attrs = match.group(2) or ""
            
            if tag not in self.ALLOWED_TAGS:
                return ''  # Remove disallowed tag
            
            # Filter attributes
            allowed_attrs = self.ALLOWED_ATTRIBUTES.get(tag, [])
            filtered_attrs = self._filter_attributes(attrs, allowed_attrs)
            
            if tag in ['img', 'br']:
                return f'<{tag}{filtered_attrs}>'
            return f'<{tag}{filtered_attrs}>'
        
        # Match opening tags
        pattern = r'<(\w+)([^>]*)>'
        return re.sub(pattern, tag_replacer, html_content, flags=re.IGNORECASE)
    
    def _filter_attributes(self, attrs: str, allowed: list) -> str:
        """Filter HTML attributes."""
        if not allowed:
            return ""
        
        result = []
        # Match attribute="value" or attribute='value' or attribute
        pattern = r'(\w+)\s*(?:=\s*["\']?([^"\'>\s]+)["\']?)?'
        
        for match in re.finditer(pattern, attrs):
            name = match.group(1).lower()
            value = match.group(2) or ""
            
            if name in allowed:
                # Sanitize URL attributes
                if name in ['href', 'src']:
                    value = self._sanitize_url(value)
                
                if value:
                    result.append(f'{name}="{html.escape(value)}"')
                else:
                    result.append(name)
        
        return ' ' + ' '.join(result) if result else ''
    
    def _sanitize_url(self, url: str) -> str:
        """Sanitize URL to prevent javascript: injection."""
        if not url:
            return ""
        
        url = url.strip()
        url_lower = url.lower()
        
        # Block dangerous protocols
        dangerous = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']
        for proto in dangerous:
            if url_lower.startswith(proto):
                return ""
        
        # Allow only http/https/mailto/tel
        allowed = ['http://', 'https://', 'mailto:', 'tel:', '#', '/']
        if not any(url_lower.startswith(a) for a in allowed):
            return ""
        
        return url
    
    @staticmethod
    def escape_html(text: str) -> str:
        """
        Escape HTML entities.
        
        Use for plain text output in HTML context.
        
        Args:
            text: Plain text
        
        Returns:
            Escaped HTML
        """
        return html.escape(text) if text else ""
    
    @staticmethod
    def escape_js(text: str) -> str:
        """
        Escape for JavaScript context.
        
        Args:
            text: String to escape
        
        Returns:
            JS-escaped string
        """
        if not text:
            return ""
        
        escapes = {
            '\\': '\\\\',
            '"': '\\"',
            "'": "\\'",
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '<': '\\x3c',
            '>': '\\x3e'
        }
        
        return ''.join(escapes.get(c, c) for c in text)
    
    @staticmethod
    def escape_css(text: str) -> str:
        """
        Escape for CSS context.
        
        Args:
            text: String to escape
        
        Returns:
            CSS-escaped string
        """
        if not text:
            return ""
        
        # CSS escaping
        result = []
        for c in text:
            if ord(c) < 32 or c in ['"', "'", '\\', '<', '>', '&', ';']:
                result.append(f'\\{ord(c):06x}')
            else:
                result.append(c)
        
        return ''.join(result)


# Alias for consistent naming with other security modules
XSSProtection = XSSFilter
