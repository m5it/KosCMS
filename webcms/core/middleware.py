"""
WebCMS Middleware System

Request/response processing pipeline.
"""

from typing import Callable, List, Optional
from .request import Request
from .response import Response


class MiddlewareStack:
    """Middleware execution stack."""
    
    def __init__(self):
        self.middlewares: List[Callable] = []
    
    def add(self, middleware: Callable) -> None:
        """Add middleware to stack."""
        self.middlewares.append(middleware)
    
    def process(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """
        Process request through middleware chain.
        
        Args:
            request: HTTP request
            handler: Final request handler
        
        Returns:
            HTTP response
        """
        # Build chain from inside out
        wrapped = handler
        for middleware in reversed(self.middlewares):
            wrapped = self._wrap(middleware, wrapped)
        
        return wrapped(request)
    
    def _wrap(
        self,
        middleware: Callable,
        next_handler: Callable[[Request], Response]
    ) -> Callable[[Request], Response]:
        """Wrap handler with middleware."""
        def wrapper(request: Request) -> Response:
            return middleware(request, next_handler)
        return wrapper


class CommonMiddleware:
    """Common middleware for all requests."""
    
    def __init__(self, app=None):
        self.app = app
    
    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Process request."""
        # Add common headers
        response = handler(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        return response


class CORSMiddleware:
    """CORS handling middleware."""
    
    def __init__(
        self,
        allow_origins: List[str] = None,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None
    ):
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["Content-Type", "Authorization"]
    
    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Handle CORS."""
        if request.method == "OPTIONS":
            # Preflight request
            return Response(
                "",
                200,
                headers={
                    "Access-Control-Allow-Origin": ", ".join(self.allow_origins),
                    "Access-Control-Allow-Methods": ", ".join(self.allow_methods),
                    "Access-Control-Allow-Headers": ", ".join(self.allow_headers)
                }
            )
        
        response = handler(request)
        response.headers["Access-Control-Allow-Origin"] = self.allow_origins[0]
        return response