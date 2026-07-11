"""
Content Indexer

Indexes content models for full-text search.
"""

import re
from typing import Optional

from .engine import SearchEngine


class ContentIndexer:
    """Indexes content for search."""
    
    def __init__(self, engine: Optional[SearchEngine] = None):
        self.engine = engine or SearchEngine()
    
    def _clean_text(self, html: str) -> str:
        """Strip HTML tags and normalize whitespace."""
        # Simple HTML tag removal
        text = re.sub(r'<[^>]+>', '', html)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    
    def _generate_excerpt(self, content: str, length: int = 200) -> str:
        """Generate excerpt from content."""
        text = self._clean_text(content)
        if len(text) <= length:
            return text
        return text[:length].rsplit(' ', 1)[0] + "..."
    
    def index_post(self, post) -> bool:
        """Index a Post model."""
        content_type = "post"
        content_id = f"post:{post.id}"
        
        clean_content = self._clean_text(post.content)
        excerpt = post.excerpt or self._generate_excerpt(post.content)
        
        return self.engine.index_document(
            content_id=content_id,
            content_type=content_type,
            title=post.title,
            content=clean_content,
            excerpt=excerpt
        )
    
    def index_page(self, page) -> bool:
        """Index a Page model."""
        content_id = f"page:{page.id}"
        clean_content = self._clean_text(page.content)
        excerpt = page.excerpt or self._generate_excerpt(page.content)
        
        return self.engine.index_document(
            content_id=content_id,
            content_type="page",
            title=page.title,
            content=clean_content,
            excerpt=excerpt
        )
    
    def remove_content(self, content_id: str, content_type: str) -> bool:
        """Remove content from index."""
        full_id = f"{content_type}:{content_id}"
        return self.engine.remove_document(full_id)
    
    def reindex_all(self, posts, pages):
        """Reindex all content."""
        self.engine.clear_index()
        
        indexed = 0
        for post in posts:
            if self.index_post(post):
                indexed += 1
        
        for page in pages:
            if self.index_page(page):
                indexed += 1
        
        return indexed
