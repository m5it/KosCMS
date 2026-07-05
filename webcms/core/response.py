"""
WebCMS Response wrapper

Convenient response creation with JSON, HTML, error support.
"""

import json
from typing import Dict, List, Optional, Any, Union, Callable


class Response:
    """HTTP Response wrapper."""
    
    def __init__(
        self,
        body: Union[str, bytes, Dict, List] = "",
        status: int = 200,
        headers: Optional[Dict[str, str]] = None,
        content_type: str = "text/html; charset=utf-8"
    ):
        self.status = status
        self.headers = headers or {}
        self.content_type = content_type
        
        if isinstance(body, (dict, list)):
            self.body = json.dumps(body).encode("utf-8")
            self.content_type = "application/json"
        elif isinstance(body, str):
            self.body = body.encode("utf-8")
        else:
            self.body = body
        
        self.headers.setdefault("Content-Type", self.content_type)
        self.headers.setdefault("Content-Length", str(len(self.body)))
    
    def to_wsgi(self, start_response: Callable) -> List[bytes]:
        """Convert to WSGI response."""
        status_line = f"{self.status} {self._get_status_text(self.status)}"
        header_list = [(k, str(v)) for k, v in self.headers.items()]
        
        start_response(status_line, header_list)
        return [self.body]
    
    @classmethod
    def html(cls, content: str, status: int = 200) -> "Response":
        """Create HTML response."""
        return cls(content, status, content_type="text/html; charset=utf-8")
    
    @classmethod
    def json(cls, data: Any, status: int = 200) -> "Response":
        """Create JSON response."""
        return cls(data, status, content_type="application/json")
    
    @classmethod
    def text(cls, content: str, status: int = 200) -> "Response":
        """Create plain text response."""
        return cls(content, status, content_type="text/plain; charset=utf-8")
    
    @classmethod
    def redirect(cls, location: str, status: int = 302) -> "Response":
        """Create redirect response."""
        return cls("", status, headers={"Location": location})
    
    @classmethod
    def not_found(cls, message: str = "Not Found") -> "Response":
        """Create 404 response."""
        return cls(message, 404)
    
    @classmethod
    def error(cls, message: str = "Internal Server Error", status: int = 500) -> "Response":
        """Create error response."""
        return cls(message, status)
    
    @classmethod
    def forbidden(cls, message: str = "Forbidden") -> "Response":
        """Create 403 response."""
        return cls(message, 403)
    
    @classmethod
    def unauthorized(cls, message: str = "Unauthorized") -> "Response":
        """Create 401 response."""
        return cls(message, 401)
    
    def _get_status_text(self, code: int) -> str:
        """Get HTTP status text."""
        statuses = {
            200: "OK",
            201: "Created",
            301: "Moved Permanently",
            302: "Found",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            500: "Internal Server Error"
        }
        return statuses.get(code, "Unknown")
    
    def __repr__(self) -> str:
        return f"<Response {self.status}>"