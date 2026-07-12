"""
REST API

Flask-RESTful style API for admin operations.
"""

import json
from typing import Dict, List, Callable
from datetime import datetime

from webcms.core.request import Request
from webcms.core.response import Response
from webcms.content.search_service import SearchService
from webcms.content.exchange import ContentExporter, ContentImporter, ExportOptions
from webcms.plugins.marketplace import get_registry
from webcms.cache.manager import get_tenant_cache, CacheWarmer
from webcms.admin.widgets import get_widget_registry, WidgetConfig
from webcms.security.middleware import CSPReportHandler
from webcms.admin.admin_api import register_admin_api


class APIEndpoint:
    """Base API endpoint."""
    
    methods = ["GET"]
    
    def __init__(self, db=None, auth=None):
        self.db = db
        self.auth = auth
    
    def dispatch(self, request: Request, **kwargs) -> Response:
        """Dispatch to handler method."""
        method = request.method
        
        if method == "GET":
            return self.get(request, **kwargs)
        elif method == "POST":
            return self.post(request, **kwargs)
        elif method == "PUT":
            return self.put(request, **kwargs)
        elif method == "DELETE":
            return self.delete(request, **kwargs)
        
        return Response.error("Method not allowed", 405)
    
    def get(self, request: Request, **kwargs) -> Response:
        return Response.error("Not implemented", 501)
    
    def post(self, request: Request, **kwargs) -> Response:
        return Response.error("Not implemented", 501)
    
    def put(self, request: Request, **kwargs) -> Response:
        return Response.error("Not implemented", 501)
    
    def delete(self, request: Request, **kwargs) -> Response:
        return Response.error("Not implemented", 501)


class DashboardStats(APIEndpoint):
    """Dashboard statistics endpoint."""
    
    def get(self, request: Request) -> Response:
        """Get dashboard stats."""
        from webcms.models.user import User
        from webcms.models.content import Post, Page
        from webcms.models.media import Media
        
        stats = {
            "users": {
                "total": self.db.query(User).filter(User.is_deleted == False).count(),
                "active": self.db.query(User).filter(
                    User.is_deleted == False,
                    User.is_active == True
                ).count()
            },
            "content": {
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
                "pages": self.db.query(Page).filter(Page.is_deleted == False).count()
            },
            "media": {
                "total_files": self.db.query(Media).filter(Media.is_deleted == False).count()
            },
            "system": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.1.0"
            }
        }
        
        return Response.json(stats)


class PostList(APIEndpoint):
    """Posts CRUD endpoint."""
    
    methods = ["GET", "POST"]
    
    def get(self, request: Request) -> Response:
        """List posts."""
        from webcms.content.repository import PostRepository
        
        repo = PostRepository(self.db)
        limit = int(request.get_param("limit", 20))
        offset = int(request.get_param("offset", 0))
        
        posts = repo.list_published(limit=limit, offset=offset)
        
        result = []
        for post in posts:
            result.append({
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "status": post.status,
                "published_at": post.published_at.isoformat() if post.published_at else None,
                "author": post.author.display_name if post.author else None,
                "is_featured": post.is_featured
            })
        
        return Response.json({"posts": result, "total": len(result)})
    
    def post(self, request: Request) -> Response:
        """Create post."""
        from webcms.content.manager import ContentManager
        
        data = request.json
        if not data:
            return Response.error("Invalid JSON", 400)
        
        manager = ContentManager(self.db)
        
        try:
            post = manager.create_post(
                title=data.get("title"),
                slug=data.get("slug"),
                content=data.get("content"),
                author_id=data.get("author_id"),
                status=data.get("status", "draft"),
                excerpt=data.get("excerpt"),
                category_ids=data.get("category_ids", []),
                tags=data.get("tags", [])
            )
            
            return Response.json({"id": post.id, "message": "Post created"}, 201)
            
        except Exception as e:
            return Response.error(str(e), 400)


class PostDetail(APIEndpoint):
    """Single post operations."""
    
    methods = ["GET", "PUT", "DELETE"]
    
    def get(self, request: Request, post_id: str) -> Response:
        """Get post details."""
        from webcms.content.repository import PostRepository
        
        repo = PostRepository(self.db)
        post = repo.get_by_id(post_id)
        
        if not post:
            return Response.not_found()
        
        return Response.json({
            "id": post.id,
            "title": post.title,
            "slug": post.slug,
            "content": post.content,
            "excerpt": post.excerpt,
            "status": post.status,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "author": {"id": post.author.id, "name": post.author.display_name} if post.author else None,
            "categories": [{"id": c.id, "name": c.name} for c in post.categories],
            "tags": [{"id": t.id, "name": t.name} for t in post.tags]
        })
    
    def put(self, request: Request, post_id: str) -> Response:
        """Update post."""
        from webcms.content.manager import ContentManager
        
        data = request.json
        if not data:
            return Response.error("Invalid JSON", 400)
        
        manager = ContentManager(self.db)
        post = manager.update_post(post_id, **data)
        
        if not post:
            return Response.not_found()
        
        return Response.json({"id": post.id, "message": "Post updated"})
    
    def delete(self, request: Request, post_id: str) -> Response:
        """Delete post."""
        from webcms.content.manager import ContentManager
        
        manager = ContentManager(self.db)
        
        if manager.delete_post(post_id):
            return Response.json({"message": "Post deleted"})
        
        return Response.not_found()


class UserList(APIEndpoint):
    """Users CRUD endpoint."""
    
    methods = ["GET", "POST"]
    
    def get(self, request: Request) -> Response:
        """List users."""
        from webcms.models.user import User
        
        users = self.db.query(User).filter(
            User.is_deleted == False
        ).order_by(User.created_at.desc()).limit(50).all()
        
        result = []
        for user in users:
            result.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "is_active": user.is_active,
                "roles": [r.name for r in user.roles]
            })
        
        return Response.json({"users": result})


class MediaList(APIEndpoint):
    """Media endpoint."""
    
    methods = ["GET"]
    
    def get(self, request: Request) -> Response:
        """List media files."""
        from webcms.models.media import Media
        
        media = self.db.query(Media).filter(
            Media.is_deleted == False
        ).order_by(Media.created_at.desc()).limit(50).all()
        
        result = []
        for m in media:
            result.append({
                "id": m.id,
                "filename": m.filename,
                "url": m.file_url,
                "mime_type": m.mime_type,
                "width": m.width,
                "height": m.height
            })
        
        return Response.json({"media": result})


class SearchEndpoint(APIEndpoint):
    """Search content."""
    
    methods = ["GET"]
    
    def get(self, request: Request) -> Response:
        """Search content."""
        query = request.get_param("q", "")
        if not query:
            return Response.json({"query": "", "total": 0, "results": []})
        
        service = SearchService(self.db)
        results = service.search(
            query=query,
            content_type=request.get_param("type", None),
            limit=min(int(request.get_param("limit", 20)), 100)
        )
        
        return Response.json(results)


class ContentExportEndpoint(APIEndpoint):
    """Export content endpoint."""
    
    methods = ["POST"]
    
    def post(self, request: Request) -> Response:
        """Export content."""
        data = request.json or {}
        
        options = ExportOptions(
            format=data.get("format", "json"),
            content_types=data.get("content_types", ["post", "page"]),
            status=data.get("status"),
            author_id=data.get("author_id")
        )
        
        try:
            exporter = ContentExporter(self.db)
            result = exporter.export(options)
            
            content_type = "application/json" if options.format == "json" else "text/csv"
            return Response(result, 200, {"Content-Type": content_type})
            
        except Exception as e:
            return Response.error(f"Export failed: {str(e)}", 500)


class ContentImportEndpoint(APIEndpoint):
    """Import content endpoint."""
    
    methods = ["POST"]
    
    def post(self, request: Request) -> Response:
        """Import content."""
        if not request.json and not request.body:
            return Response.error("No data provided", 400)
        
        data = json.dumps(request.json) if request.json else request.body.decode('utf-8')
        format_hint = request.get_param("format", None)
        
        try:
            importer = ContentImporter(self.db)
            result = importer.import_content(data, format_hint)
            
            return Response.json({
                "success": result.success,
                "imported": result.imported,
                "skipped": result.skipped,
                "errors": result.errors
            }, 200 if result.success else 400)
            
        except Exception as e:
            return Response.error(f"Import failed: {str(e)}", 500)


class PluginMarketplaceEndpoint(APIEndpoint):
    """Plugin marketplace endpoint."""
    
    methods = ["GET"]
    
    def get(self, request: Request) -> Response:
        """List available plugins."""
        registry = get_registry()
        
        tag = request.get_param("tag", None)
        installed_only = request.get_param("installed", "false").lower() == "true"
        
        plugins = registry.list_available(tag=tag, installed_only=installed_only)
        
        result = []
        for plugin in plugins:
            result.append({
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
                "installed": plugin.installed,
                "active": plugin.active,
                "compatible": registry.check_compatibility(plugin)[0]
            })
        
        return Response.json({"plugins": result})


class PluginInstallEndpoint(APIEndpoint):
    """Plugin install/uninstall endpoint."""
    
    methods = ["POST", "DELETE"]
    
    def post(self, request: Request) -> Response:
        """Install or activate plugin."""
        data = request.json or {}
        plugin_name = data.get("name") or request.get_param("name", "")
        action = data.get("action", "install")
        
        if not plugin_name:
            return Response.error("Plugin name required", 400)
        
        registry = get_registry()
        
        if action == "install":
            source = data.get("source")
            success, message = registry.install(plugin_name, source)
        elif action == "activate":
            success, message = registry.activate(plugin_name)
        else:
            return Response.error("Invalid action", 400)
        
        return Response.json({"success": success, "message": message}, 
                           200 if success else 400)
    
    def delete(self, request: Request) -> Response:
        """Uninstall or deactivate plugin."""
        plugin_name = request.get_param("name", "")
        action = request.get_param("action", "uninstall")
        
        if not plugin_name:
            return Response.error("Plugin name required", 400)
        
        registry = get_registry()
        
        if action == "uninstall":
            success, message = registry.uninstall(plugin_name)
        elif action == "deactivate":
            success, message = registry.deactivate(plugin_name)
        else:
            return Response.error("Invalid action", 400)
        
        return Response.json({"success": success, "message": message},
                           200 if success else 400)


class CacheStatsEndpoint(APIEndpoint):
    """Cache management endpoint."""
    
    methods = ["GET", "POST"]
    
    def get(self, request: Request) -> Response:
        """Get cache stats."""
        tenant_id = request.get_param("tenant", "default")
        cache = get_tenant_cache(tenant_id)
        
        return Response.json({
            "tenant": tenant_id,
            "stats": cache.get_stats() if hasattr(cache, 'get_stats') else {}
        })
    
    def post(self, request: Request) -> Response:
        """Clear or warm cache."""
        data = request.json or {}
        action = data.get("action", "warm")
        tenant_id = data.get("tenant", "default")
        tag = data.get("tag")
        
        cache = get_tenant_cache(tenant_id)
        
        if action == "clear":
            if tag:
                count = cache.tag_invalidate(tag)
                return Response.json({"action": "clear", "tag": tag, "cleared": count})
            else:
                cache.clear()
                return Response.json({"action": "clear_all"})
        
        elif action == "warm":
            return Response.json({
                "action": "warm",
                "message": "Use CacheWarmer.register() to define warming functions"
            })
        
        return Response.error("Invalid action", 400)


class AdminWidgetsEndpoint(APIEndpoint):
    """Admin widgets endpoint."""
    
    methods = ["GET"]
    
    def get(self, request: Request) -> Response:
        """Get dashboard widgets."""
        registry = get_widget_registry()
        
        configs = [
            WidgetConfig(id="stats", title="Content Statistics", 
                        type="stats", position="main"),
            WidgetConfig(id="activity", title="Recent Activity", 
                        type="activity", position="main", refresh_interval=60),
            WidgetConfig(id="health", title="System Health", 
                        type="health", position="sidebar", refresh_interval=30),
        ]
        
        widgets = registry.render_all(self.db, configs)
        
        return Response.json({"widgets": widgets})


class CSPReportEndpoint(APIEndpoint):
    """CSP violation reporting endpoint."""
    
    methods = ["POST"]
    
    def __init__(self, db=None, auth=None):
        super().__init__(db, auth)
        self.handler = CSPReportHandler()
    
    def post(self, request: Request) -> Response:
        """Handle CSP report."""
        return self.handler(request)


def create_api(app, db, auth):
    """Register API routes."""
    
    endpoints = [
        ("/api/v1/dashboard", DashboardStats),
        ("/api/v1/posts", PostList),
        ("/api/v1/posts/<post_id>", PostDetail),
        ("/api/v1/users", UserList),
        ("/api/v1/media", MediaList),
        ("/api/v1/search", SearchEndpoint),
        ("/api/v1/content/export", ContentExportEndpoint),
        ("/api/v1/content/import", ContentImportEndpoint),
        ("/api/v1/plugins/marketplace", PluginMarketplaceEndpoint),
        ("/api/v1/plugins/install", PluginInstallEndpoint),
        ("/api/v1/cache/stats", CacheStatsEndpoint),
        ("/api/v1/admin/widgets", AdminWidgetsEndpoint),
        ("/api/v1/security/csp-report", CSPReportEndpoint),
    ]
    
    for path, endpoint_class in endpoints:
        endpoint = endpoint_class(db=db, auth=auth)
        
        def handler(request, **kwargs):
            return endpoint.dispatch(request, **kwargs)
        
        app.router.add(path, handler, endpoint_class.methods)
    
    # Register the React admin panel /api/v1/admin/* endpoints
    register_admin_api(app, db=db, auth=auth)
    
    return app
