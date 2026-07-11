
"""
Tests for Content Exchange Module (v1.1.0)

Import/Export functionality with JSON and CSV formats.
"""

import pytest
import json
import tempfile
from io import StringIO
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from webcms.content.exchange import (
    ContentExporter, 
    ContentImporter, 
    ExportOptions,
    ImportResult
)
from webcms.models.content import Post, Page, Category, Tag
from webcms.models.base import Base


class TestContentExporter:
    """Test content export functionality."""
    
    @pytest.fixture
    def db(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test data
        post = Post(
            id="post-1",
            title="Test Post",
            slug="test-post",
            content="Test content",
            status="published"
        )
        page = Page(
            id="page-1",
            title="Test Page",
            slug="test-page",
            content="Page content",
            status="published"
        )
        
        session.add_all([post, page])
        session.commit()
        
        yield session
        session.close()
    
    def test_export_json(self, db):
        """Test JSON export."""
        exporter = ContentExporter(db)
        options = ExportOptions(format="json")
        
        result = exporter.export(options)
        
        assert isinstance(result, str)
        data = json.loads(result)
        assert "posts" in data
        assert "pages" in data
        assert len(data["posts"]) == 1
        assert data["posts"][0]["title"] == "Test Post"
    
    def test_export_csv(self, db):
        """Test CSV export."""
        exporter = ContentExporter(db)
        options = ExportOptions(format="csv")
        
        result = exporter.export(options)
        
        assert isinstance(result, str)
        assert "type,id,title" in result
        assert "post,post-1,Test Post" in result
    
    def test_export_filter_by_status(self, db):
        """Test export with status filter."""
        # Add draft post
        draft = Post(
            id="post-2",
            title="Draft Post",
            slug="draft-post",
            content="Draft",
            status="draft"
        )
        db.add(draft)
        db.commit()
        
        exporter = ContentExporter(db)
        options = ExportOptions(format="json", status="published")
        
        result = exporter.export(options)
        data = json.loads(result)
        
        # Should only export published
        assert len(data["posts"]) == 1
    
    def test_export_filter_by_type(self, db):
        """Test export with content type filter."""
        exporter = ContentExporter(db)
        options = ExportOptions(format="json", content_types=["post"])
        
        result = exporter.export(options)
        data = json.loads(result)
        
        assert len(data["posts"]) == 1
        assert len(data["pages"]) == 0


class TestContentImporter:
    """Test content import functionality."""
    
    @pytest.fixture
    def db(self):
        """Create test database session."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_import_json(self, db):
        """Test JSON import."""
        importer = ContentImporter(db)
        
        data = {
            "posts": [{
                "title": "Imported Post",
                "slug": "imported-post",
                "content": "Imported content",
                "status": "published"
            }],
            "pages": [{
                "title": "Imported Page",
                "slug": "imported-page",
                "content": "Page content",
                "status": "published"
            }]
        }
        
        result = importer.import_content(json.dumps(data))
        
        assert result.success is True
        assert result.imported == 2
    
    def test_import_csv(self, db):
        """Test CSV import."""
        importer = ContentImporter(db)
        
        csv_data = """type,id,title,slug,content,excerpt,status,created_at,author_id
post,post-1,Test Post,test-post,Content,,published,2024-01-01,user-1
page,page-1,Test Page,test-page,Page content,,published,2024-01-01,user-1"""
        
        result = importer.import_content(csv_data)
        
        assert result.success is True
        assert result.imported == 2
    
    def test_import_duplicate_slug(self, db):
        """Test import with duplicate slug handling."""
        importer = ContentImporter(db)
        
        # Import first time
        data = {
            "posts": [{
                "title": "Test Post",
                "slug": "test-post",
                "content": "Content",
                "status": "published"
            }]
        }
        importer.import_content(json.dumps(data))
        
        # Import again (should skip)
        result = importer.import_content(json.dumps(data))
        
        assert result.skipped == 1
        assert "already exists" in result.errors[0]
    
    def test_import_validation(self, db):
        """Test import validation."""
        importer = ContentImporter(db)
        
        # Missing required field
        data = {
            "posts": [{
                "title": "Invalid Post"
                # Missing slug and content
            }]
        }
        
        result = importer.import_content(json.dumps(data))
        
        assert result.success is False
        assert result.skipped == 1
    
    def test_detect_format_json(self, db):
        """Test JSON format detection."""
        importer = ContentImporter(db)
        
        json_data = '{"posts": []}'
        format_type = importer.detect_format(json_data)
        
        assert format_type == "json"
    
    def test_detect_format_csv(self, db):
        """Test CSV format detection."""
        importer = ContentImporter(db)
        
        csv_data = "type,title,slug\npost,Test,test"
        format_type = importer.detect_format(csv_data)
        
        assert format_type == "csv"


class TestImportResult:
    """Test import result dataclass."""
    
    def test_import_result_creation(self):
        """Test ImportResult creation."""
        result = ImportResult(
            success=True,
            imported=5,
            errors=[],
            skipped=0
        )
        
        assert result.success is True
        assert result.imported == 5
