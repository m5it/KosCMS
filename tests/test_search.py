
"""
Tests for Search Module (v1.1.0)

Full-text search with SQLite FTS5 integration.
"""

import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from webcms.search.engine import SearchEngine, SearchResult
from webcms.search.indexer import ContentIndexer
from webcms.content.search_service import SearchService
from webcms.models.content import Post, Page
from webcms.models.base import Base


class TestSearchEngine:
    """Test FTS5 search engine."""
    
    @pytest.fixture
    def engine(self):
        """Create test database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        
        yield engine
        
        os.unlink(db_path)
    
    @pytest.fixture
    def db(self, engine):
        """Create database session."""
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_index_document(self, db):
        """Test document indexing."""
        search_engine = SearchEngine(db_path=":memory:")
        
        result = search_engine.index_document(
            content_id="post:1",
            content_type="post",
            title="Test Post",
            content="This is test content",
            excerpt="Test excerpt"
        )
        
        assert result is True
    
    def test_search(self, db):
        """Test search functionality."""
        search_engine = SearchEngine(db_path=":memory:")
        
        # Index documents
        search_engine.index_document(
            content_id="post:1",
            content_type="post",
            title="Python Tutorial",
            content="Learn Python programming",
            excerpt="Python basics"
        )
        
        search_engine.index_document(
            content_id="post:2",
            content_type="post",
            title="JavaScript Guide",
            content="Learn JavaScript programming",
            excerpt="JS basics"
        )
        
        # Search
        results = search_engine.search("Python")
        
        assert len(results) == 1
        assert results[0].content_id == "post:1"
        assert results[0].title == "Python Tutorial"
    
    def test_remove_document(self, db):
        """Test document removal."""
        search_engine = SearchEngine(db_path=":memory:")
        
        search_engine.index_document(
            content_id="post:1",
            content_type="post",
            title="Test Post",
            content="Content",
            excerpt="Excerpt"
        )
        
        result = search_engine.remove_document("post:1")
        assert result is True
        
        results = search_engine.search("Test")
        assert len(results) == 0


class TestContentIndexer:
    """Test content indexer."""
    
    def test_clean_text(self):
        """Test HTML cleaning."""
        indexer = ContentIndexer()
        
        html = "<p>Hello <strong>World</strong></p>"
        clean = indexer._clean_text(html)
        
        assert clean == "Hello World"
    
    def test_generate_excerpt(self):
        """Test excerpt generation."""
        indexer = ContentIndexer()
        
        content = "This is a very long content that should be truncated"
        excerpt = indexer._generate_excerpt(content, length=20)
        
        assert len(excerpt) <= 25  # Allow for ellipsis
        assert excerpt.endswith("...")


class TestSearchService:
    """Test search service integration."""
    
    @pytest.fixture
    def engine(self):
        """Create test database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        
        yield engine
        
        os.unlink(db_path)
    
    @pytest.fixture
    def db(self, engine):
        """Create database session."""
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_index_content(self, db):
        """Test indexing content."""
        service = SearchService(db)
        
        # Create test post
        post = Post(
            id="test-post-1",
            title="Test Post",
            slug="test-post",
            content="Test content",
            status="published"
        )
        db.add(post)
        db.commit()
        
        result = service.index_content(post)
        assert result is True
    
    def test_search_integration(self, db):
        """Test full search integration."""
        service = SearchService(db)
        
        # Create and index posts
        post1 = Post(
            id="post-1",
            title="Python Guide",
            slug="python-guide",
            content="Learn Python",
            status="published"
        )
        post2 = Post(
            id="post-2",
            title="JavaScript Guide",
            slug="js-guide",
            content="Learn JavaScript",
            status="published"
        )
        
        db.add_all([post1, post2])
        db.commit()
        
        service.index_content(post1)
        service.index_content(post2)
        
        # Search
        results = service.search("Python")
        
        assert results["total"] == 1
        assert results["results"][0]["content"].title == "Python Guide"
    
    def test_remove_from_index(self, db):
        """Test removing from index."""
        service = SearchService(db)
        
        post = Post(
            id="post-1",
            title="Test",
            slug="test",
            content="Content",
            status="published"
        )
        db.add(post)
        db.commit()
        
        service.index_content(post)
        result = service.remove_from_index("post-1", "post")
        
        assert result is True
