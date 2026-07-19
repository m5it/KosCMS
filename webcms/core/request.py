"""
WebCMS Request wrapper

Wraps WSGI environ with convenient access to request data.
"""

import io
import json
import urllib.parse
from email.parser import BytesParser
from email.message import Message
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("webcms.request")


class Request:
    """HTTP Request wrapper."""
    
    # Maximum allowed body size (50 MB by default). Requests with a larger
    # Content-Length are rejected, and body reads are capped to this size.
    MAX_BODY_SIZE = 50 * 1024 * 1024
    
    def __init__(self, environ: Dict[str, Any]):
        self.environ = environ
        self.method = environ.get("REQUEST_METHOD", "GET")
        self.path = environ.get("PATH_INFO", "/")
        self.query_string = environ.get("QUERY_STRING", "")
        self.content_type = environ.get("CONTENT_TYPE", "")
        self.content_length = self._parse_content_length(environ.get("CONTENT_LENGTH"))
        
        self._headers: Optional[Dict[str, str]] = None
        self._query_params: Optional[Dict[str, List[str]]] = None
        self._body: Optional[bytes] = None
        self._json: Optional[Any] = None
        self._form: Optional[Dict[str, Any]] = None
        self._files: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_wsgi(cls, environ: Dict[str, Any]) -> "Request":
        """Create Request from WSGI environ."""
        return cls(environ)
    
    @staticmethod
    def _parse_content_length(value: Any) -> int:
        """
        Safely parse CONTENT_LENGTH from the WSGI environ.

        Returns 0 for missing/invalid/negative values, and caps the value
        at MAX_BODY_SIZE to prevent memory exhaustion.
        """
        if value is None or value == "":
            return 0
        try:
            length = int(value)
        except (ValueError, TypeError):
            logger.debug("Invalid Content-Length value: %r", value)
            return 0
        if length < 0:
            logger.debug("Negative Content-Length: %s", length)
            return 0
        if length > Request.MAX_BODY_SIZE:
            logger.warning("Content-Length %s exceeds max body size; capping", length)
            return Request.MAX_BODY_SIZE
        return length
    
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
            try:
                self._query_params = urllib.parse.parse_qs(
                    self.query_string,
                    keep_blank_values=True
                )
            except Exception as exc:
                logger.debug("Failed to parse query string: %s", exc)
                self._query_params = {}
        return self._query_params
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get single query parameter."""
        params = self.query_params.get(name, [])
        return params[0] if params else default
    
    @property
    def body(self) -> bytes:
        """Get request body safely."""
        if self._body is None:
            try:
                if self.content_length > 0:
                    self._body = self.environ["wsgi.input"].read(self.content_length)
                else:
                    self._body = b""
            except (OSError, ValueError) as exc:
                logger.debug("Error reading request body: %s", exc)
                self._body = b""
            except Exception as exc:
                logger.warning("Unexpected error reading request body: %s", exc)
                self._body = b""
        return self._body
    
    @property
    def json(self) -> Optional[Any]:
        """Parse JSON body safely."""
        if self._json is None and self.body:
            if self.content_type.startswith("application/json"):
                try:
                    self._json = json.loads(self.body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    logger.debug("Failed to parse JSON body: %s", exc)
                    self._json = None
                except Exception as exc:
                    logger.warning("Unexpected error parsing JSON body: %s", exc)
                    self._json = None
        return self._json
    
    @property
    def form(self) -> Dict[str, Any]:
        """Parse form data safely."""
        self._parse_multipart()
        return self._form or {}

    @property
    def files(self) -> Dict[str, Any]:
        """Parse uploaded files safely."""
        self._parse_multipart()
        return self._files or {}

    def _parse_multipart(self):
        """Parse multipart/form-data into form fields and files."""
        if self._form is not None and self._files is not None:
            return
        self._form = {}
        self._files = {}
        if self.content_type.startswith("application/x-www-form-urlencoded"):
            try:
                self._form = urllib.parse.parse_qs(
                    self.body.decode("utf-8"),
                    keep_blank_values=True
                )
            except UnicodeDecodeError as exc:
                logger.debug("Invalid UTF-8 in form body: %s", exc)
            except Exception as exc:
                logger.warning("Unexpected error parsing form body: %s", exc)
        elif self.content_type.startswith("multipart/form-data"):
            try:
                # Parse using email BytesParser which handles multipart bodies
                msg = BytesParser().parsebytes(self.body)
                if msg.is_multipart():
                    for part in msg.get_payload():
                        if not isinstance(part, Message):
                            continue
                        disp = part.get("Content-Disposition", "")
                        name = None
                        filename = None
                        for piece in disp.split(";"):
                            piece = piece.strip()
                            if piece.startswith("name="):
                                name = piece[5:].strip('"')
                            elif piece.startswith("filename="):
                                filename = piece[9:].strip('"')
                        if not name:
                            continue
                        content = part.get_payload(decode=True) or b""
                        if filename:
                            self._files[name] = {
                                "filename": filename,
                                "content": content,
                                "content_type": part.get("Content-Type", "application/octet-stream"),
                            }
                        else:
                            self._form[name] = content.decode("utf-8", errors="replace")
            except Exception as exc:
                logger.warning("Error parsing multipart form data: %s", exc)
    
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
