"""
Security Middleware

HTTPS redirect and security headers.
"""

from typing import Callable
from webcms.core.request import Request
from webcms.core.response import Response


class SecurityMiddleware:
    """Add security headers to responses."""
    
    def __init__(
        self,
        content_security_policy: str = None,
        strict_transport_security: bool = True,
        frame_options: str = "DENY",
        content_type_options: bool = True,
        xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin"
    ):
        self.csp = content_security_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'"
        )
        self.hsts = strict_transport_security
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
    
    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Process request and add security headers."""
        response = handler(request)
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp
        
        # Strict Transport Security
        if self.hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.frame_options
        
        # X-Content-Type-Options
        if self.content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = self.referrer_policy
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )
        
        return response


class HTTPSRedirectMiddleware:
    """Redirect HTTP to HTTPS."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Redirect to HTTPS if needed."""
        # Check if request is secure
        is_secure = (
            request.environ.get("wsgi.url_scheme") == "https" or
            request.environ.get("HTTP_X_FORWARDED_PROTO") == "https"
        )
        
        if self.enabled and not is_secure:
            # Build HTTPS URL
            host = request.environ.get("HTTP_HOST", "localhost")
            path = request.environ.get("PATH_INFO", "/")
            query = request.environ.get("QUERY_STRING", "")
            
            https_url = f"https://{host}{path}"
            if query:
                https_url += f"?{query}"
            
            return Response.redirect(https_url, 301)
        
        return handler(request)