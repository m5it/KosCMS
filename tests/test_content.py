"""
Content Management Tests
"""

import pytest
from datetime import datetime

from webcms.models.content import Page, Post, Category, Tag
from webcms.content.manager import ContentManager


def test_create_page(db_session):
    """Test page creation."""
    manager = ContentManager(db_session)
    
    page = manager.create_page(
        title="Test Page",
        slug="test-page",
        content="<p>Hello World</p>",
        author_id="user-123",
        status="published",
        is_homepage=True
    )
    
    assert page.title == "Test Page"
    assert page.slug == "test-page"
    assert page.is_homepage is True
    assert page.status == "published"


def test_create_post(db_session):
    """Test post creation."""
    manager = ContentManager(db_session)
    
    post = manager.create_post(
        title="Test Post",
        slug="test-post",
        content="# Markdown Content",
        author_id="user-123",
        status="draft",
        format="markdown"
    )
    
    assert post.title == "Test Post"
    assert post.format == "markdown"
    assert post.status == "draft"


def test_post_categories(db_session):
    """Test post with categories."""
    # Create category
    from webcms.models.content import Category
    cat = Category(name="Tech", slug="tech")
    db_session.add(cat)
    db_session.commit()
    
    manager = ContentManager(db_session)
    post = manager.create_post(
        title="Tech Post",
        slug="tech-post",
        content="Content",
        author_id="user-123",
        category_ids=[cat.id]
    )
    
    assert len(post.categories) == 1
    assert post.categories[0].name == "Tech"


def test_soft_delete(db_session):
    """Test soft delete."""
    manager = ContentManager(db_session)
    
    post = manager.create_post(
        title="To Delete",
        slug="to-delete",
        content="Content",
        author_id="user-123"
    )
    
    # Soft delete
    assert manager.delete_post(post.id, soft=True) is True
    
    # Should not appear in list
    posts = manager.list_posts()
    assert post.id not in [p.id for p in posts]
    
    # But still in DB
    from webcms.models.content import Post
    found = db_session.query(Post).filter(Post.id == post.id).first()
    assert found.is_deleted is True


def test_slug_generation():
    """Test slug is unique."""
    pass  # Would test slug uniqueness logic