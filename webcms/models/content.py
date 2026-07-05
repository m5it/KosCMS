"""
Content Models

Pages, Posts, Categories, Tags with relationships.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from .base import Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin


# Association table for Post-Tag many-to-many
post_tags = Table(
    'post_tags',
    Base.metadata,
    Column('post_id', String(36), ForeignKey('posts.id'), primary_key=True),
    Column('tag_id', String(36), ForeignKey('tags.id'), primary_key=True)
)


# Association table for Post-Category many-to-many
post_categories = Table(
    'post_categories',
    Base.metadata,
    Column('post_id', String(36), ForeignKey('posts.id'), primary_key=True),
    Column('category_id', String(36), ForeignKey('categories.id'), primary_key=True)
)


class Page(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Static page model."""
    
    __tablename__ = 'pages'
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    
    status = Column(String(20), default='draft', nullable=False)  # draft, published, archived
    published_at = Column(DateTime, nullable=True)
    
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    is_homepage = Column(Boolean, default=False, nullable=False)
    template = Column(String(100), default='page.html', nullable=False)
    
    # Relationships
    author_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    author = relationship('User', back_populates='pages', 
                       foreign_keys=[author_id])
    
    def __repr__(self):
        return f"<Page {self.title}>"


class Post(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """Blog post model."""
    
    __tablename__ = 'posts'
    
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    format = Column(String(20), default='markdown', nullable=False)  # markdown, html
    
    status = Column(String(20), default='draft', nullable=False)  # draft, published, scheduled, archived
    published_at = Column(DateTime, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    
    featured_image_id = Column(String(36), ForeignKey('media.id'), nullable=True)
    featured_image = relationship('Media', foreign_keys=[featured_image_id])
    
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    
    view_count = Column(String(20), default='0', nullable=False)
    comment_count = Column(String(20), default='0', nullable=False)
    
    allow_comments = Column(Boolean, default=True, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    is_sticky = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    author_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    author = relationship('User', back_populates='posts',
                       foreign_keys=[author_id])
    
    categories = relationship('Category', secondary=post_categories,
                             back_populates='posts')
    tags = relationship('Tag', secondary=post_tags,
                       back_populates='posts')
    
    def __repr__(self):
        return f"<Post {self.title}>"


class Category(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Content category model."""
    
    __tablename__ = 'categories'
    
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    parent_id = Column(String(36), ForeignKey('categories.id'), nullable=True)
    parent = relationship('Category', remote_side='Category.id',
                       backref='children')
    
    # Relationships
    posts = relationship('Post', secondary=post_categories,
                        back_populates='categories')
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Tag(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Content tag model."""
    
    __tablename__ = 'tags'
    
    name = Column(String(50), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    
    # Relationships
    posts = relationship('Post', secondary=post_tags,
                        back_populates='tags')
    
    def __repr__(self):
        return f"<Tag {self.name}>"


class PostTag:
    """Post-Tag association."""
    pass