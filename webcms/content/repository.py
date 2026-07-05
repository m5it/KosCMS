"""
Content Repository

Data access layer for content operations.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from webcms.models.content import Page, Post, Category, Tag


class PageRepository:
    """Page data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, page_id: str) -> Optional[Page]:
        """Get page by ID."""
        return self.db.query(Page).options(
            joinedload(Page.author)
        ).filter(
            Page.id == page_id,
            Page.is_deleted == False
        ).first()
    
    def get_by_slug(self, slug: str) -> Optional[Page]:
        """Get page by slug."""
        return self.db.query(Page).options(
            joinedload(Page.author)
        ).filter(
            Page.slug == slug,
            Page.is_deleted == False
        ).first()
    
    def get_homepage(self) -> Optional[Page]:
        """Get homepage."""
        return self.db.query(Page).filter(
            Page.is_homepage == True,
            Page.is_deleted == False,
            Page.status == "published"
        ).first()
    
    def list_published(self, limit: int = 100) -> List[Page]:
        """List published pages."""
        return self.db.query(Page).filter(
            Page.status == "published",
            Page.is_deleted == False
        ).order_by(Page.title).limit(limit).all()


class PostRepository:
    """Post data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, post_id: str) -> Optional[Post]:
        """Get post by ID with relationships."""
        return self.db.query(Post).options(
            joinedload(Post.author),
            joinedload(Post.categories),
            joinedload(Post.tags)
        ).filter(
            Post.id == post_id,
            Post.is_deleted == False
        ).first()
    
    def get_by_slug(self, slug: str) -> Optional[Post]:
        """Get post by slug."""
        return self.db.query(Post).options(
            joinedload(Post.author),
            joinedload(Post.categories),
            joinedload(Post.tags)
        ).filter(
            Post.slug == slug,
            Post.is_deleted == False
        ).first()
    
    def list_published(self, limit: int = 10, offset: int = 0) -> List[Post]:
        """List published posts."""
        from datetime import datetime
        return self.db.query(Post).filter(
            Post.status == "published",
            Post.is_deleted == False,
            Post.published_at <= datetime.utcnow()
        ).order_by(
            Post.is_sticky.desc(),
            Post.published_at.desc()
        ).offset(offset).limit(limit).all()
    
    def list_by_category(self, category_slug: str, limit: int = 10) -> List[Post]:
        """List posts by category."""
        return self.db.query(Post).join(Post.categories).filter(
            Category.slug == category_slug,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(Post.published_at.desc()).limit(limit).all()
    
    def list_by_tag(self, tag_slug: str, limit: int = 10) -> List[Post]:
        """List posts by tag."""
        return self.db.query(Post).join(Post.tags).filter(
            Tag.slug == tag_slug,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(Post.published_at.desc()).limit(limit).all()
    
    def get_featured(self, limit: int = 5) -> List[Post]:
        """Get featured posts."""
        return self.db.query(Post).filter(
            Post.is_featured == True,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(Post.published_at.desc()).limit(limit).all()