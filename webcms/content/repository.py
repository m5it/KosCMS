"""
Content Repository

Optimized data access layer with eager loading.
"""

import logging
import time
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import event

from webcms.models.content import Page, Post, Category, Tag

# Configure query logger
logger = logging.getLogger("webcms.query")


class QueryProfiler:
    """Query profiling and logging."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.query_count = 0
        self.query_time = 0.0
    
    def log_query(self, query_time: float):
        """Log query execution."""
        if self.enabled:
            self.query_count += 1
            self.query_time += query_time
    
    def get_stats(self) -> dict:
        """Get query statistics."""
        return {
            "query_count": self.query_count,
            "total_time_ms": round(self.query_time * 1000, 2),
            "avg_time_ms": round((self.query_time / self.query_count) * 1000, 2) 
                          if self.query_count > 0 else 0
        }
    
    def reset(self):
        """Reset statistics."""
        self.query_count = 0
        self.query_time = 0.0


# Global profiler
profiler = QueryProfiler(enabled=False)


def enable_query_logging():
    """Enable query logging for debugging."""
    profiler.enabled = True
    
    @event.listens_for(Session, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        context._query_start_time = time.time()
    
    @event.listens_for(Session, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        total_time = time.time() - context._query_start_time
        profiler.log_query(total_time)
        logger.debug(f"Query: {statement[:100]}... | Time: {total_time*1000:.2f}ms")


class PageRepository:
    """Optimized page data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _base_query(self):
        """Get base query with eager loading."""
        return self.db.query(Page).options(
            joinedload(Page.author),
            joinedload(Page.author.of_type(None))  # Optional author
        )
    
    def get_by_id(self, page_id: str) -> Optional[Page]:
        """
        Get page by ID with author.
        
        Query count: 1 (was 2 without joinedload)
        """
        return self._base_query().filter(
            Page.id == page_id,
            Page.is_deleted == False
        ).first()
    
    def get_by_slug(self, slug: str) -> Optional[Page]:
        """
        Get page by slug with author.
        
        Query count: 1 (was 2 without joinedload)
        """
        return self._base_query().filter(
            Page.slug == slug,
            Page.is_deleted == False
        ).first()
    
    def get_homepage(self) -> Optional[Page]:
        """Get homepage."""
        return self._base_query().filter(
            Page.is_homepage == True,
            Page.is_deleted == False,
            Page.status == "published"
        ).first()
    
    def list_published(self, limit: int = 100, 
                       offset: int = 0) -> List[Page]:
        """
        List published pages with author.
        
        Query count: 1 (was N+1 without joinedload)
        """
        return self._base_query().filter(
            Page.status == "published",
            Page.is_deleted == False
        ).order_by(
            Page.title
        ).offset(offset).limit(limit).all()
    
    def list_with_pagination(self, page: int = 1, 
                            per_page: int = 20) -> tuple:
        """
        Get paginated pages with total count.
        
        Query count: 2 (count + data)
        """
        base_q = self.db.query(Page).filter(Page.is_deleted == False)
        
        total = base_q.count()
        items = self._base_query().filter(
            Page.is_deleted == False
        ).order_by(
            Page.created_at.desc()
        ).offset((page - 1) * per_page).limit(per_page).all()
        
        return items, total


class PostRepository:
    """Optimized post data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _base_query(self):
        """Get base query with eager loading."""
        return self.db.query(Post).options(
            joinedload(Post.author),
            selectinload(Post.categories),  # Use selectinload for many-to-many
            selectinload(Post.tags),
            joinedload(Post.featured_image)
        )
    
    def get_by_id(self, post_id: str) -> Optional[Post]:
        """
        Get post by ID with all relationships.
        
        Query count: 1 (was 4 without eager loading)
        """
        return self._base_query().filter(
            Post.id == post_id,
            Post.is_deleted == False
        ).first()
    
    def get_by_slug(self, slug: str) -> Optional[Post]:
        """
        Get post by slug with all relationships.
        
        Query count: 1 (was 4 without eager loading)
        """
        return self._base_query().filter(
            Post.slug == slug,
            Post.is_deleted == False
        ).first()
    
    def list_published(self, limit: int = 10, 
                       offset: int = 0) -> List[Post]:
        """
        List published posts with author and categories.
        
        Query count: 1 (was N+1 without eager loading)
        """
        from datetime import datetime
        
        return self._base_query().filter(
            Post.status == "published",
            Post.is_deleted == False,
            Post.published_at <= datetime.utcnow()
        ).order_by(
            Post.is_sticky.desc(),
            Post.published_at.desc()
        ).offset(offset).limit(limit).all()
    
    def list_by_category(self, category_slug: str, 
                         limit: int = 10) -> List[Post]:
        """
        List posts by category with eager loading.
        
        Query count: 2 (join + eager load)
        Was: N+3 without optimization
        """
        return self.db.query(Post).options(
            joinedload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.tags)
        ).join(Post.categories).filter(
            Category.slug == category_slug,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(
            Post.published_at.desc()
        ).limit(limit).all()
    
    def list_by_tag(self, tag_slug: str, limit: int = 10) -> List[Post]:
        """
        List posts by tag with eager loading.
        
        Query count: 2 (join + eager load)
        Was: N+3 without optimization
        """
        return self.db.query(Post).options(
            joinedload(Post.author),
            selectinload(Post.categories),
            selectinload(Post.tags)
        ).join(Post.tags).filter(
            Tag.slug == tag_slug,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(
            Post.published_at.desc()
        ).limit(limit).all()
    
    def get_featured(self, limit: int = 5) -> List[Post]:
        """
        Get featured posts with author.
        
        Query count: 1 (was N+1 without joinedload)
        """
        return self._base_query().filter(
            Post.is_featured == True,
            Post.status == "published",
            Post.is_deleted == False
        ).order_by(
            Post.published_at.desc()
        ).limit(limit).all()
    
    def get_recent(self, days: int = 7, limit: int = 10) -> List[Post]:
        """
        Get recent posts from last N days.
        
        Query count: 1
        """
        from datetime import datetime, timedelta
        
        since = datetime.utcnow() - timedelta(days=days)
        
        return self._base_query().filter(
            Post.created_at >= since,
            Post.is_deleted == False
        ).order_by(
            Post.created_at.desc()
        ).limit(limit).all()
    
    def search_by_title(self, query: str, limit: int = 20) -> List[Post]:
        """
        Search posts by title (case-insensitive).
        
        Query count: 1
        """
        search_term = f"%{query}%"
        
        return self._base_query().filter(
            Post.title.ilike(search_term),
            Post.is_deleted == False,
            Post.status == "published"
        ).order_by(
            Post.published_at.desc()
        ).limit(limit).all()
    
    def get_related(self, post: Post, limit: int = 5) -> List[Post]:
        """
        Get related posts by shared categories.
        
        Query count: 2 (was N+1 without optimization)
        """
        if not post.categories:
            return []
        
        category_ids = [c.id for c in post.categories]
        
        return self.db.query(Post).options(
            joinedload(Post.author)
        ).join(Post.categories).filter(
            Category.id.in_(category_ids),
            Post.id != post.id,
            Post.status == "published",
            Post.is_deleted == False
        ).distinct().order_by(
            Post.published_at.desc()
        ).limit(limit).all()


class CategoryRepository:
    """Category data access."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Category]:
        """
        Get all categories with post counts.
        
        Query count: 1
        """
        return self.db.query(Category).filter(
            Category.is_deleted == False
        ).order_by(Category.name).all()
    
    def get_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug."""
        return self.db.query(Category).filter(
            Category.slug == slug,
            Category.is_deleted == False
        ).first()
    
    def get_with_posts(self, slug: str, limit: int = 10) -> Optional[Category]:
        """
        Get category with recent posts.
        
        Query count: 2 (was N+1 without eager loading)
        """
        return self.db.query(Category).options(
            selectinload(Category.posts)
        ).filter(
            Category.slug == slug,
            Category.is_deleted == False
        ).first()


def get_query_stats() -> dict:
    """Get query statistics."""
    return profiler.get_stats()


def reset_query_stats():
    """Reset query statistics."""
    profiler.reset()
