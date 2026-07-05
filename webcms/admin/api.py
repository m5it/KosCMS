"""
REST API

Flask-RESTful style API for admin operations.
"""

import json
from typing import Dict, List, Callable
from datetime import datetime

from webcms.core.request import Request
from webcms.core.response import Response


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
        # Get counts
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
                "version": "1.0.0"
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
        
        # Pagination
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
        
        return Response.json({
            "posts": result,
            "total": len(result)
        })
    
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
            
            return Response.json({
                "id": post.id,
                "message": "Post created"
            }, 201)
            
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
            "format": post.format,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "author": {
                "id": post.author.id,
                "name": post.author.display_name
            } if post.author else None,
            "categories": [{"id": c.id, "name": c.name} for c in post.categories],
            "tags": [{"id": t.id, "name": t.name} for t in post.tags],
            "is_featured": post.is_featured,
            "allow_comments": post.allow_comments
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
        
        return Response.json({
            "id": post.id,
            "message": "Post updated"
        })
    
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
                "is_superuser": user.is_superuser,
                "roles": [r.name for r in user.roles],
                "created_at": user.created_at.isoformat()
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
                "size": m.file_size,
                "mime_type": m.mime_type,
                "width": m.width,
                "height": m.height,
                "created_at": m.created_at.isoformat()
            })
        
        return Response.json({"media": result})


def create_api(app, db, auth):
    """Register API routes."""
    
    endpoints = [
        ("/api/v1/dashboard", DashboardStats),
        ("/api/v1/posts", PostList),
        ("/api/v1/posts/<post_id>", PostDetail),
        ("/api/v1/users", UserList),
        ("/api/v1/media", MediaList),
    ]
    
    for path, endpoint_class in endpoints:
        endpoint = endpoint_class(db=db, auth=auth)
        
        def handler(request, **kwargs):
            return endpoint.dispatch(request, **kwargs)
        
        # Register with app router
        app.router.add(path, handler, endpoint_class.methods)
    
    return app