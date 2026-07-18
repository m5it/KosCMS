"""
WebCMS Middleware System

Request/response processing pipeline.
"""

import re
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


class RequestValidationMiddleware:
    """
    Early request validation middleware.

    Rejects malformed requests, null bytes, control characters, invalid
    HTTP versions, and HTTP/2 PRI requests before they reach application
    logic. This provides defense in depth even when the WSGI server
    accepts the connection.
    """

    # Valid HTTP methods per RFC 7231 and common extensions.
    VALID_METHODS = {
        "GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH",
        "TRACE", "CONNECT",
    }

    # Reject paths containing null bytes or most control characters.
    _invalid_path_re = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

    def __init__(self, max_request_line: int = 8192, max_path_length: int = 4096):
        self.max_request_line = max_request_line
        self.max_path_length = max_path_length

    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Validate request and either reject it or pass it on."""
        reason = self._validate(request)
        if reason:
            return Response.json({"error": reason}, 400)
        return handler(request)

    def _validate(self, request: Request) -> Optional[str]:
        """Return an error string if the request should be rejected."""
        method = request.method
        path = request.path
        query = request.query_string

        # Validate HTTP method
        if not method or not method.isupper() or method not in self.VALID_METHODS:
            return "Invalid HTTP method"

        # Reject HTTP/2 PRI requests
        if method == "PRI":
            return "HTTP/2 not supported"

        # Validate path
        if not path.startswith("/"):
            return "Invalid request path"
        if len(path) > self.max_path_length:
            return "Request path too long"
        if self._invalid_path_re.search(path):
            return "Invalid characters in request path"

        # Validate query string
        if self._invalid_path_re.search(query):
            return "Invalid characters in query string"

        # Validate SERVER_PROTOCOL / HTTP version if available
        server_protocol = request.environ.get("SERVER_PROTOCOL", "")
        if server_protocol and not self._valid_http_version(server_protocol):
            return "Invalid HTTP version"

        # Validate content length header
        content_length = request.environ.get("CONTENT_LENGTH", "")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return "Invalid Content-Length header"
            if length < 0:
                return "Invalid Content-Length header"
            if length > 50 * 1024 * 1024:  # 50 MB default cap
                return "Request body too large"

        return None

    @staticmethod
    def _valid_http_version(version: str) -> bool:
        """Check that SERVER_PROTOCOL is a supported HTTP version."""
        return version in ("HTTP/1.0", "HTTP/1.1")


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
