
"""
Tests for Admin Widgets (v1.1.0)

Dashboard widget framework.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from webcms.admin.widgets import (
    WidgetBase,
    StatsWidget,
    RecentActivityWidget,
    SystemHealthWidget,
    WidgetRegistry,
    WidgetConfig,
    get_widget_registry
)
from webcms.models.content import Post, Page
from webcms.models.user import User
from webcms.models.base import Base


class TestWidgetConfig:
    """Test widget configuration."""
    
    def test_config_creation(self):
        """Test WidgetConfig creation."""
        config = WidgetConfig(
            id="test-widget",
            title="Test Widget",
            type="test",
            position="main",
            refresh_interval=60
        )
        
        assert config.id == "test-widget"
        assert config.title == "Test Widget"
        assert config.refresh_interval == 60


class TestStatsWidget:
    """Test stats widget."""
    
    @pytest.fixture
    def db(self):
        """Create test database."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create test data
        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            display_name="Test User"
        )
        post = Post(
            id="post-1",
            title="Test Post",
            slug="test-post",
            content="Content",
            status="published",
            author_id="user-1"
        )
        page = Page(
            id="page-1",
            title="Test Page",
            slug="test-page",
            content="Page content",
            status="published",
            author_id="user-1"
        )
        
        session.add_all([user, post, page])
        session.commit()
        
        yield session
        session.close()
    
    def test_render(self, db):
        """Test stats widget rendering."""
        widget = StatsWidget(db)
        data = widget.render()
        
        assert "stats" in data
        assert data["stats"]["posts"]["total"] == 1
        assert data["stats"]["pages"] == 1
        assert data["stats"]["users"] == 1


class TestRecentActivityWidget:
    """Test recent activity widget."""
    
    @pytest.fixture
    def db(self):
        """Create test database."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            display_name="Test User"
        )
        post = Post(
            id="post-1",
            title="Recent Post",
            slug="recent-post",
            content="Content",
            status="published",
            author_id="user-1"
        )
        
        session.add_all([user, post])
        session.commit()
        
        yield session
        session.close()
    
    def test_render(self, db):
        """Test activity widget rendering."""
        widget = RecentActivityWidget(db)
        data = widget.render()
        
        assert "activities" in data
        assert len(data["activities"]) > 0


class TestSystemHealthWidget:
    """Test system health widget."""
    
    @pytest.fixture
    def db(self):
        """Create test database."""
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()
    
    def test_render(self, db):
        """Test health widget rendering."""
        widget = SystemHealthWidget(db)
        data = widget.render()
        
        assert "status" in data
        assert "checks" in data
        assert "timestamp" in data


class TestWidgetRegistry:
    """Test widget registry."""
    
    def test_register_widget(self):
        """Test widget registration."""
        registry = WidgetRegistry()
        
        class TestWidget(WidgetBase):
            def render(self):
                return {"test": "data"}
        
        registry.register("test", TestWidget)
        
        assert "test" in registry._widgets
    
    def test_list_widgets(self):
        """Test listing widgets."""
        registry = WidgetRegistry()
        widgets = registry.list_widgets()
        
        # Should have default widgets
        assert len(widgets) > 0
    
    def test_unregister_widget(self):
        """Test widget unregistration."""
        registry = WidgetRegistry()
        
        class TestWidget(WidgetBase):
            def render(self):
                return {}
        
        registry.register("temp", TestWidget)
        registry.unregister("temp")
        
        assert "temp" not in registry._widgets


class TestGlobalWidgetRegistry:
    """Test global widget registry."""
    
    def test_singleton(self):
        """Test singleton pattern."""
        reg1 = get_widget_registry()
        reg2 = get_widget_registry()
        
        assert reg1 is reg2
