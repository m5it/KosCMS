"""
Content Manager

CRUD operations for pages and posts with KosDB support.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    from sqlalchemy.orm import Session
    from webcms.models.content import Page, Post, Category, Tag
    from webcms.models.user import User
    from webcms.content.search_service import SearchService
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False


class ContentManager:
    """Content management operations with KosDB fallback."""
    
    def __init__(self, db=None):
        self.db = db
        self._kosdb_manager = None
        
        # Check if db is KosDB
        if db and self._is_kosdb():
            from .manager_kosdb import KosDBContentManager
            self._kosdb_manager = KosDBContentManager(db)
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _is_sqlalchemy(self) -> bool:
        """Check if database is SQLAlchemy."""
        if not HAS_SQLALCHEMY:
            return False
        return hasattr(self.db, 'query') and callable(getattr(self.db, 'query'))
    
    def list_posts(self, status: Optional[str] = None,
                   limit: int = 20, offset: int = 0) -> List[Dict]:
        """List posts with pagination."""
        if self._kosdb_manager:
            return self._kosdb_manager.list_posts(status, limit, offset)
        
        if not HAS_SQLALCHEMY or not self._is_sqlalchemy():
            return []
        
        query = self.db.query(Post).filter(Post.is_deleted == False)
        if status:
            query = query.filter(Post.status == status)
        return query.order_by(Post.created_at.desc()).offset(offset).limit(limit).all()
    
    def list_pages(self, status: Optional[str] = None,
                   limit: int = 20, offset: int = 0) -> List[Dict]:
        """List pages with pagination."""
        if self._kosdb_manager:
            return self._kosdb_manager.list_pages(status, limit, offset)
        
        if not HAS_SQLALCHEMY or not self._is_sqlalchemy():
            return []
        
        query = self.db.query(Page).filter(Page.is_deleted == False)
        if status:
            query = query.filter(Page.status == status)
        return query.order_by(Page.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_page(self, page_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Dict]:
        """Get page by ID or slug."""
        if self._kosdb_manager:
            return self._kosdb_manager.get_page(page_id, slug)
        
        if not HAS_SQLALCHEMY or not self._is_sqlalchemy():
            return None
        
        if page_id:
            return self.db.query(Page).filter(
                Page.id == page_id,
                Page.is_deleted == False
            ).first()
        if slug:
            return self.db.query(Page).filter(
                Page.slug == slug,
                Page.is_deleted == False
            ).first()
        return None
    
    def get_post(self, post_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Dict]:
        """Get post by ID or slug."""
        if self._kosdb_manager:
            return self._kosdb_manager.get_post(post_id, slug)
        
        if not HAS_SQLALCHEMY or not self._is_sqlalchemy():
            return None
        
        if post_id:
            return self.db.query(Post).filter(
                Post.id == post_id,
                Post.is_deleted == False
            ).first()
        if slug:
            return self.db.query(Post).filter(
                Post.slug == slug,
                Post.is_deleted == False
            ).first()
        return None
    
    def create_page(self, title: str, slug: str, content: str,
                    author_id: str, **kwargs) -> Dict:
        """Create new page."""
        if self._kosdb_manager:
            return self._kosdb_manager.create_page(title, slug, content, author_id, **kwargs)
        
        if not HAS_SQLALCHEMY:
            raise RuntimeError("SQLAlchemy not available")
        
        page = Page(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            **kwargs
        )
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        return page
    
    def create_post(self, title: str, slug: str, content: str,
                    author_id: str, **kwargs) -> Dict:
        """Create new post."""
        if self._kosdb_manager:
            return self._kosdb_manager.create_post(title, slug, content, author_id, **kwargs)
        
        if not HAS_SQLALCHEMY:
            raise RuntimeError("SQLAlchemy not available")
        
        post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            **kwargs
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post
    
    def update_page(self, page_id: str, **kwargs) -> Optional[Dict]:
        """Update page."""
        if self._kosdb_manager:
            return self._kosdb_manager.update_page(page_id, **kwargs)
        
        if not HAS_SQLALCHEMY:
            return None
        
        page = self.get_page(page_id=page_id)
        if not page:
            return None
        
        for key, value in kwargs.items():
            if hasattr(page, key):
                setattr(page, key, value)
        
        page.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(page)
        return page
    
    def update_post(self, post_id: str, **kwargs) -> Optional[Dict]:
        """Update post."""
        if self._kosdb_manager:
            return self._kosdb_manager.update_post(post_id, **kwargs)
        
        if not HAS_SQLALCHEMY:
            return None
        
        post = self.get_post(post_id=post_id)
        if not post:
            return None
        
        for key, value in kwargs.items():
            if hasattr(post, key):
                setattr(post, key, value)
        
        post.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(post)
        return post
    
    def delete_page(self, page_id: str, soft: bool = True) -> bool:
        """Delete page."""
        if self._kosdb_manager:
            return self._kosdb_manager.delete_page(page_id, soft)
        
        if not HAS_SQLALCHEMY:
            return False
        
        page = self.get_page(page_id=page_id)
        if not page:
            return False
        
        if soft:
            page.soft_delete()
        else:
            self.db.delete(page)
        
        self.db.commit()
        return True
    
    def delete_post(self, post_id: str, soft: bool = True) -> bool:
        """Delete post."""
        if self._kosdb_manager:
            return self._kosdb_manager.delete_post(post_id, soft)
        
        if not HAS_SQLALCHEMY:
            return False
        
        post = self.get_post(post_id=post_id)
        if not post:
            return False
        
        if soft:
            post.soft_delete()
        else:
            self.db.delete(post)
        
        self.db.commit()
        return True
