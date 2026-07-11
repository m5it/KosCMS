
"""
Admin Widgets

Dashboard widget framework for admin panel.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session


@dataclass
class WidgetConfig:
    """Widget configuration."""
    id: str
    title: str
    type: str
    position: str = "main"  # main, sidebar, header
    refresh_interval: int = 0  # seconds, 0 = no auto-refresh
    settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}


class WidgetBase(ABC):
    """Base class for dashboard widgets."""
    
    def __init__(self, db: Session, config: Optional[WidgetConfig] = None):
        self.db = db
        self.config = config or WidgetConfig(
            id=self.__class__.__name__.lower(),
            title="Widget",
            type="base"
        )
    
    @abstractmethod
    def render(self) -> Dict[str, Any]:
        """
        Render widget data.
        
        Returns:
            Dict with widget data
        """
        pass
    
    def to_json(self) -> str:
        """Serialize widget to JSON."""
        return json.dumps({
            "id": self.config.id,
            "title": self.config.title,
            "type": self.config.type,
            "position": self.config.position,
            "refresh_interval": self.config.refresh_interval,
            "data": self.render()
        })
    
    def get_template(self) -> str:
        """Get widget HTML template."""
        return f"<div id='{self.config.id}' class='widget'></div>"


class StatsWidget(WidgetBase):
    """Content statistics widget."""
    
    def __init__(self, db: Session, config: Optional[WidgetConfig] = None):
        super().__init__(db, config)
        self.config.type = "stats"
        self.config.title = "Content Statistics"
    
    def render(self) -> Dict[str, Any]:
        """Render content stats."""
        from webcms.models.content import Post, Page
        from webcms.models.user import User
        from webcms.models.media import Media
        
        stats = {
            "posts": {
                "total": self.db.query(Post).filter(Post.is_deleted == False).count(),
                "published": self.db.query(Post).filter(
                    Post.is_deleted == False,
                    Post.status == "published"
                ).count(),
                "drafts": self.db.query(Post).filter(
                    Post.is_deleted == False,
                    Post.status == "draft"
                ).count()
            },
            "pages": self.db.query(Page).filter(Page.is_deleted == False).count(),
            "users": self.db.query(User).filter(User.is_deleted == False).count(),
            "media": self.db.query(Media).filter(Media.is_deleted == False).count()
        }
        
        return {
            "stats": stats,
            "last_updated": datetime.utcnow().isoformat()
        }


class RecentActivityWidget(WidgetBase):
    """Recent activity widget."""
    
    def __init__(self, db: Session, config: Optional[WidgetConfig] = None):
        super().__init__(db, config)
        self.config.type = "activity"
        self.config.title = "Recent Activity"
        self.config.refresh_interval = 60  # Refresh every minute
    
    def render(self) -> Dict[str, Any]:
        """Render recent activity."""
        from webcms.models.content import Post, Page
        from webcms.models.system import AuditLog
        
        # Get recent posts
        recent_posts = self.db.query(Post).filter(
            Post.is_deleted == False
        ).order_by(Post.created_at.desc()).limit(5).all()
        
        # Get recent pages
        recent_pages = self.db.query(Page).filter(
            Page.is_deleted == False
        ).order_by(Page.created_at.desc()).limit(5).all()
        
        # Get recent audit logs
        recent_logs = self.db.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(10).all()
        
        activities = []
        
        for post in recent_posts:
            activities.append({
                "type": "post",
                "action": "created",
                "title": post.title,
                "time": post.created_at.isoformat(),
                "user": post.author.display_name if post.author else "Unknown"
            })
        
        for page in recent_pages:
            activities.append({
                "type": "page",
                "action": "created",
                "title": page.title,
                "time": page.created_at.isoformat(),
                "user": page.author.display_name if page.author else "Unknown"
            })
        
        # Sort by time
        activities.sort(key=lambda x: x["time"], reverse=True)
        
        return {
            "activities": activities[:10],
            "count": len(activities)
        }


class SystemHealthWidget(WidgetBase):
    """System health widget."""
    
    def __init__(self, db: Session, config: Optional[WidgetConfig] = None):
        super().__init__(db, config)
        self.config.type = "health"
        self.config.title = "System Health"
        self.config.refresh_interval = 30  # Refresh every 30 seconds
    
    def render(self) -> Dict[str, Any]:
        """Render system health status."""
        import os
        import psutil
        
        try:
            # Get system stats
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            health = {
                "status": "healthy",
                "checks": {
                    "database": self._check_database(),
                    "memory": {
                        "status": "ok" if memory.percent < 80 else "warning",
                        "used_percent": memory.percent,
                        "available_mb": memory.available // (1024 * 1024)
                    },
                    "disk": {
                        "status": "ok" if disk.percent < 80 else "warning",
                        "used_percent": disk.percent,
                        "free_gb": disk.free // (1024 * 1024 * 1024)
                    },
                    "cpu": {
                        "status": "ok" if cpu_percent < 80 else "warning",
                        "usage_percent": cpu_percent
                    }
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Determine overall status
            statuses = [c["status"] for c in health["checks"].values() 
                       if isinstance(c, dict)]
            if any(s == "error" for s in statuses):
                health["status"] = "error"
            elif any(s == "warning" for s in statuses):
                health["status"] = "warning"
            
            return health
            
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            self.db.execute("SELECT 1")
            return {"status": "ok", "message": "Connected"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class WidgetRegistry:
    """Widget registry and loader."""
    
    def __init__(self):
        self._widgets: Dict[str, type] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default widgets."""
        self.register("stats", StatsWidget)
        self.register("activity", RecentActivityWidget)
        self.register("health", SystemHealthWidget)
    
    def register(self, widget_id: str, widget_class: type):
        """
        Register a widget class.
        
        Args:
            widget_id: Unique widget identifier
            widget_class: Widget class (must inherit WidgetBase)
        """
        if not issubclass(widget_class, WidgetBase):
            raise ValueError("Widget must inherit from WidgetBase")
        
        self._widgets[widget_id] = widget_class
    
    def unregister(self, widget_id: str):
        """Unregister a widget."""
        if widget_id in self._widgets:
            del self._widgets[widget_id]
    
    def get_widget(self, widget_id: str, db: Session, 
                   config: Optional[WidgetConfig] = None) -> Optional[WidgetBase]:
        """
        Get widget instance.
        
        Args:
            widget_id: Widget identifier
            db: Database session
            config: Optional widget configuration
        
        Returns:
            Widget instance or None
        """
        widget_class = self._widgets.get(widget_id)
        if not widget_class:
            return None
        
        return widget_class(db, config)
    
    def list_widgets(self) -> List[Dict[str, str]]:
        """List available widgets."""
        return [
            {
                "id": widget_id,
                "name": widget_class.__name__,
                "type": getattr(widget_class, 'WIDGET_TYPE', 'custom')
            }
            for widget_id, widget_class in self._widgets.items()
        ]
    
    def render_all(self, db: Session, 
                   widget_configs: List[WidgetConfig] = None) -> List[Dict]:
        """
        Render all configured widgets.
        
        Args:
            db: Database session
            widget_configs: List of widget configurations
        
        Returns:
            List of rendered widget data
        """
        if widget_configs is None:
            # Default widgets
            widget_configs = [
                WidgetConfig(id="stats", title="Statistics", type="stats"),
                WidgetConfig(id="activity", title="Activity", type="activity"),
                WidgetConfig(id="health", title="Health", type="health"),
            ]
        
        results = []
        for config in widget_configs:
            widget = self.get_widget(config.type, db, config)
            if widget:
                results.append({
                    "config": {
                        "id": config.id,
                        "title": config.title,
                        "type": config.type,
                        "position": config.position,
                        "refresh_interval": config.refresh_interval
                    },
                    "data": widget.render()
                })
        
        return results


# Global registry
_widget_registry: Optional[WidgetRegistry] = None


def get_widget_registry() -> WidgetRegistry:
    """Get or create global widget registry."""
    global _widget_registry
    if _widget_registry is None:
        _widget_registry = WidgetRegistry()
    return _widget_registry
