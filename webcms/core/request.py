"""
WebCMS Request wrapper

Wraps WSGI environ with convenient access to request data.
"""

import json
import urllib.parse
from typing import Dict, Any, Optional, List
from io import BytesIO


class Request:
    """HTTP Request wrapper."""
    
    def __init__(self, environ: Dict[str, Any]):
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.path = environ.get("PATH_INFO", "/")
        self.query_string = environ.get("QUERY_STRING", "")
        self.content_type = environ.get("CONTENT_TYPE", "")
        self.content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
        
        self._headers: Optional[Dict[str, str]] = None
        self._query_params: Optional[Dict[str, List[str]]] = None
        self._body: Optional[bytes] = None
        self._json: Optional[Any] = None
        self._form: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_wsgi(cls, environ: Dict[str, Any]) -> "Request":
        """Create Request from WSGI environ."""
        return cls(environ)
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get HTTP headers."""
        if self._headers is None:
            self._headers = {}
            for key, value in self.environ.items():
                if key.startswith("HTTP_"):
                    header_name = key[5:].replace("_", "-").title()
                    self._headers[header_name] = value
        return self._headers
    
    @property
    def query_params(self) -> Dict[str, List[str]]:
        """Get query string parameters."""
        if self._query_params is None:
            self._query_params = urllib.parse.parse_qs(self.query_string)
        return self._query_params
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get single query parameter."""
        params = self.query_params.get(name, [])
        return params[0] if params else default
    
    @property
    def body(self) -> bytes:
        """Get request body."""
        if self._body is None:
            if self.content_length > 0:
                self._body = self.environ["wsgi.input"].read(self.content_length)
            else:
                self._body = b""
        return self._body
    
    @property
    def json(self) -> Optional[Any]:
        """Parse JSON body."""
        if self._json is None and self.body:
            if self.content_type.startswith("application/json"):
                try:
                    self._json = json.loads(self.body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self._json = None
        return self._json
    
    @property
    def form(self) -> Dict[str, Any]:
        """Parse form data."""
        if self._form is None:
            self._form = {}
            if self.content_type.startswith("application/x-www-form-urlencoded"):
                self._form = urllib.parse.parse_qs(self.body.decode("utf-8"))
            elif self.content_type.startswith("multipart/form-data"):
                # Simplified - full implementation would use cgi.FieldStorage
                self._form = {}
        return self._form
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get specific header."""
        return self.headers.get(name.title(), default)
    
    @property
    def remote_addr(self) -> Optional[str]:
        """Get client IP address."""
        return self.environ.get("REMOTE_ADDR")
    
    @property
    def user_agent(self) -> Optional[str]:
        """Get User-Agent header."""
        return self.get_header("User-Agent")
    
    def __repr__(self) -> str:
        return f"<Request {self.method} {self.path}>"