"""
Search Service

High-level search operations for content.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from webcms.search.engine import SearchEngine, SearchResult
from webcms.search.indexer import ContentIndexer
from webcms.models.content import Post, Page


class SearchService:
    """Content search service."""
    
    def __init__(self, db: Session, engine: Optional[SearchEngine] = None):
        self.db = db
        self.engine = engine or SearchEngine()
        self.indexer = ContentIndexer(self.engine)
    
    def index_content(self, content) -> bool:
        """Index a content item (Post or Page)."""
        if isinstance(content, Post):
            return self.indexer.index_post(content)
        elif isinstance(content, Page):
            return self.indexer.index_page(content)
        return False
    
    def search(self, query: str, content_type: Optional[str] = None,
               limit: int = 20) -> Dict[str, Any]:
        """
        Search content.
        
        Args:
            query: Search query string
            content_type: Filter by type ('post', 'page', or None for all)
            limit: Maximum results
        
        Returns:
            Dict with results and metadata
        """
        raw_results = self.engine.search(query, limit)
        
        # Filter by content type if specified
        if content_type:
            raw_results = [r for r in raw_results 
                          if r.content_type == content_type]
        
        # Enrich results with full objects
        enriched = []
        for result in raw_results:
            item = self._enrich_result(result)
            if item:
                enriched.append({
                    "search": result,
                    "content": item
                })
        
        return {
            "query": query,
            "total": len(enriched),
            "results": enriched
        }
    
    def _enrich_result(self, result: SearchResult) -> Optional[Any]:
        """Fetch full content object for search result."""
        try:
            parts = result.content_id.split(":")
            if len(parts) != 2:
                return None
            
            content_type, content_id = parts
            
            if content_type == "post":
                return self.db.query(Post).filter(
                    Post.id == content_id,
                    Post.is_deleted == False
                ).first()
            elif content_type == "page":
                return self.db.query(Page).filter(
                    Page.id == content_id,
                    Page.is_deleted == False
                ).first()
        except Exception:
            pass
        return None
    
    def remove_from_index(self, content_id: str, content_type: str) -> bool:
        """Remove content from search index."""
        return self.indexer.remove_content(content_id, content_type)
    
    def reindex_all(self) -> int:
        """Reindex all content."""
        posts = self.db.query(Post).filter(Post.is_deleted == False).all()
        pages = self.db.query(Page).filter(Page.is_deleted == False).all()
        
        return self.indexer.reindex_all(posts, pages)
    
    def get_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """Get search suggestions based on titles."""
        results = self.engine.search(query, limit)
        return [r.title for r in results]
