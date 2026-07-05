"""
Content Manager

CRUD operations for pages and posts with revision tracking.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from webcms.models.content import Page, Post, Category, Tag
from webcms.models.user import User


class ContentManager:
    """Content management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Page Operations
    
    def create_page(self, title: str, slug: str, content: str,
                  author_id: str, **kwargs) -> Page:
        """Create new page."""
        page = Page(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            status=kwargs.get("status", "draft"),
            template=kwargs.get("template", "page.html"),
            meta_title=kwargs.get("meta_title"),
            meta_description=kwargs.get("meta_description"),
            is_homepage=kwargs.get("is_homepage", False)
        )
        
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        
        return page
    
    def get_page(self, page_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Page]:
        """Get page by ID or slug."""
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
    
    def update_page(self, page_id: str, **kwargs) -> Optional[Page]:
        """Update page."""
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
    
    def delete_page(self, page_id: str, soft: bool = True) -> bool:
        """Delete page."""
        page = self.get_page(page_id=page_id)
        if not page:
            return False
        
        if soft:
            page.soft_delete()
        else:
            self.db.delete(page)
        
        self.db.commit()
        return True
    
    def list_pages(self, status: Optional[str] = None,
                   limit: int = 20, offset: int = 0) -> List[Page]:
        """List pages with pagination."""
        query = self.db.query(Page).filter(Page.is_deleted == False)
        
        if status:
            query = query.filter(Page.status == status)
        
        return query.order_by(Page.created_at.desc()).offset(offset).limit(limit).all()
    
    # Post Operations
    
    def create_post(self, title: str, slug: str, content: str,
                    author_id: str, **kwargs) -> Post:
        """Create new post."""
        post = Post(
            title=title,
            slug=slug,
            content=content,
            author_id=author_id,
            status=kwargs.get("status", "draft"),
            format=kwargs.get("format", "markdown"),
            excerpt=kwargs.get("excerpt"),
            meta_title=kwargs.get("meta_title"),
            meta_description=kwargs.get("meta_description"),
            allow_comments=kwargs.get("allow_comments", True),
            is_featured=kwargs.get("is_featured", False),
            is_sticky=kwargs.get("is_sticky", False)
        )
        
        # Set published date if publishing
        if post.status == "published":
            post.published_at = datetime.utcnow()
        
        # Add categories
        category_ids = kwargs.get("category_ids", [])
        for cat_id in category_ids:
            category = self.db.query(Category).get(cat_id)
            if category:
                post.categories.append(category)
        
        # Add tags
        tag_names = kwargs.get("tags", [])
        for tag_name in tag_names:
            tag = self._get_or_create_tag(tag_name)
            post.tags.append(tag)
        
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def get_post(self, post_id: Optional[str] = None,
                 slug: Optional[str] = None) -> Optional[Post]:
        """Get post by ID or slug."""
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
    
    def update_post(self, post_id: str, **kwargs) -> Optional[Post]:
        """Update post."""
        post = self.get_post(post_id=post_id)
        if not post:
            return None
        
        for key, value in kwargs.items():
            if hasattr(post, key) and key not in ["categories", "tags"]:
                setattr(post, key, value)
        
        # Update categories
        if "category_ids" in kwargs:
            post.categories = []
            for cat_id in kwargs["category_ids"]:
                category = self.db.query(Category).get(cat_id)
                if category:
                    post.categories.append(category)
        
        # Update tags
        if "tags" in kwargs:
            post.tags = []
            for tag_name in kwargs["tags"]:
                tag = self._get_or_create_tag(tag_name)
                post.tags.append(tag)
        
        # Set published date if publishing
        if kwargs.get("status") == "published" and not post.published_at:
            post.published_at = datetime.utcnow()
        
        post.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(post)
        
        return post
    
    def delete_post(self, post_id: str, soft: bool = True) -> bool:
        """Delete post."""
        post = self.get_post(post_id=post_id)
        if not post:
            return False
        
        if soft:
            post.soft_delete()
        else:
            self.db.delete(post)
        
        self.db.commit()
        return True
    
    def list_posts(self, category_id: Optional[str] = None,
                   tag_id: Optional[str] = None,
                   status: Optional[str] = "published",
                   limit: int = 20, offset: int = 0) -> List[Post]:
        """List posts with filters."""
        query = self.db.query(Post).filter(Post.is_deleted == False)
        
        if status:
            query = query.filter(Post.status == status)
        
        if category_id:
            query = query.join(Post.categories).filter(Category.id == category_id)
        
        if tag_id:
            query = query.join(Post.tags).filter(Tag.id == tag_id)
        
        return query.order_by(Post.published_at.desc()).offset(offset).limit(limit).all()
    
    def _get_or_create_tag(self, name: str) -> Tag:
        """Get existing tag or create new one."""
        from webcms.plugins.hooks import HookManager
        slug = name.lower().replace(" ", "-")
        
        tag = self.db.query(Tag).filter(Tag.slug == slug).first()
        if not tag:
            tag = Tag(name=name, slug=slug)
            self.db.add(tag)
            self.db.flush()
        
        return tag
    
    # Category Operations
    
    def create_category(self, name: str, slug: str,
                        description: str = None,
                        parent_id: str = None) -> Category:
        """Create category."""
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id
        )
        
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        
        return category
    
    def get_categories(self) -> List[Category]:
        """Get all categories."""
        return self.db.query(Category).filter(
            Category.is_deleted == False
        ).order_by(Category.name).all()
    
    # Search
    
    def search_content(self, query: str, limit: int = 20) -> Dict[str, List]:
        """Search pages and posts."""
        search_term = f"%{query}%"
        
        pages = self.db.query(Page).filter(
            Page.is_deleted == False,
            Page.status == "published",
            (Page.title.ilike(search_term) | Page.content.ilike(search_term))
        ).limit(limit).all()
        
        posts = self.db.query(Post).filter(
            Post.is_deleted == False,
            Post.status == "published",
            (Post.title.ilike(search_term) | Post.content.ilike(search_term))
        ).limit(limit).all()
        
        return {"pages": pages, "posts": posts}