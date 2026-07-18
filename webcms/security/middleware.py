
"""
Security Middleware

HTTPS redirect, CSP, and security headers.
"""

import secrets
import json
import time
from typing import Callable, Dict, Optional, List
from dataclasses import dataclass, field
from webcms.core.request import Request
from webcms.core.response import Response


@dataclass
class CSPConfig:
    """Content Security Policy configuration."""
    
    default_src: List[str] = field(default_factory=lambda: ["'self'"])
    script_src: List[str] = field(default_factory=lambda: ["'self'"])
    style_src: List[str] = field(default_factory=lambda: ["'self'", "'unsafe-inline'"])
    img_src: List[str] = field(default_factory=lambda: ["'self'", "data:", "https:"])
    font_src: List[str] = field(default_factory=lambda: ["'self'"])
    connect_src: List[str] = field(default_factory=lambda: ["'self'"])
    media_src: List[str] = field(default_factory=lambda: ["'self'"])
    object_src: List[str] = field(default_factory=lambda: ["'none'"])
    frame_src: List[str] = field(default_factory=lambda: ["'none'"])
    frame_ancestors: List[str] = field(default_factory=lambda: ["'self'"])
    form_action: List[str] = field(default_factory=lambda: ["'self'"])
    base_uri: List[str] = field(default_factory=lambda: ["'self'"])
    report_uri: Optional[str] = None
    report_only: bool = False
    upgrade_insecure: bool = True
    
    def build_policy(self, nonce: Optional[str] = None, allow_inline: bool = False) -> str:
        """Build CSP header value."""
        directives = []
        
        # Build script-src with optional nonce or unsafe-inline
        script_sources = self.script_src.copy()
        if nonce:
            script_sources.append(f"'nonce-{nonce}'")
        if allow_inline:
            script_sources.append("'unsafe-inline'")
            script_sources.append("'unsafe-hashes'")
        
        policy_map = {
            "default-src": self.default_src,
            "script-src": script_sources,
            "style-src": self.style_src,
            "img-src": self.img_src,
            "font-src": self.font_src,
            "connect-src": self.connect_src,
            "media-src": self.media_src,
            "object-src": self.object_src,
            "frame-src": self.frame_src,
            "frame-ancestors": self.frame_ancestors,
            "form-action": self.form_action,
            "base-uri": self.base_uri,
        }
        
        for directive, sources in policy_map.items():
            if sources:
                directives.append(f"{directive} {' '.join(sources)}")
        
        if self.upgrade_insecure:
            directives.append("upgrade-insecure-requests")
        
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")
        
        return "; ".join(directives)


class NonceGenerator:
    """Generate nonces for inline scripts/styles."""
    
    def __init__(self):
        self._nonces: Dict[str, str] = {}
    
    def generate(self, request_id: str) -> str:
        """Generate a new nonce."""
        nonce = secrets.token_urlsafe(16)
        self._nonces[request_id] = nonce
        return nonce
    
    def get(self, request_id: str) -> Optional[str]:
        """Get nonce for request."""
        return self._nonces.get(request_id)
    
    def verify(self, request_id: str, nonce: str) -> bool:
        """Verify a nonce."""
        return self._nonces.get(request_id) == nonce
    
    def cleanup(self, request_id: str):
        """Remove nonce after request."""
        self._nonces.pop(request_id, None)


class SecurityHeadersMiddleware:
    """Comprehensive security headers middleware."""
    
    def __init__(
        self,
        csp_config: Optional[CSPConfig] = None,
        hsts_enabled: bool = True,
        hsts_max_age: int = 31536000,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = True,
        frame_options: str = "SAMEORIGIN",
        content_type_options: bool = True,
        xss_protection: bool = True,
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[Dict] = None,
        generate_nonces: bool = True
    ):
        self.csp_config = csp_config or CSPConfig()
        self.hsts_enabled = hsts_enabled
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.frame_options = frame_options
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or {
            "accelerometer": [],
            "camera": [],
            "geolocation": [],
            "gyroscope": [],
            "magnetometer": [],
            "microphone": [],
            "payment": [],
            "usb": []
        }
        self.generate_nonces = generate_nonces
        self.nonce_generator = NonceGenerator()
    
    def __call__(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """Process request and add security headers."""
        path = getattr(request, 'path', '/')
        is_admin = path.startswith('/admin')
        
        # Generate nonce for this request, but not for admin paths which use external scripts
        request_id = getattr(request, 'id', 'default')
        request_nonce = None
        if self.generate_nonces and not is_admin:
            request_nonce = self.nonce_generator.generate(request_id)
            request.csp_nonce = request_nonce
        
        # Process request
        response = handler(request)
        
        # Build CSP with nonce, but preserve admin responses that set their own CSP
        existing_csp = response.headers.get("Content-Security-Policy")
        if is_admin and existing_csp:
            pass
        else:
            # For admin paths, allow inline scripts (needed for event handlers)
            allow_inline = is_admin
            csp_value = self.csp_config.build_policy(request_nonce, allow_inline=allow_inline)
            if self.csp_config.report_only:
                response.headers["Content-Security-Policy-Report-Only"] = csp_value
            else:
                response.headers["Content-Security-Policy"] = csp_value
        
        # Strict Transport Security - skip for admin paths so the UI works over plain HTTP
        if self.hsts_enabled and not is_admin:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
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
        if self.permissions_policy:
            perms = []
            for feature, allowlist in self.permissions_policy.items():
                if allowlist:
                    allow_str = ' '.join(allowlist)
                    perms.append(f"{feature}=({allow_str})")
                else:
                    perms.append(f"{feature}=()")
            response.headers["Permissions-Policy"] = ", ".join(perms)
        
        # Cleanup nonce
        if self.generate_nonces:
            self.nonce_generator.cleanup(request_id)
        
        return response


class CSPReportHandler:
    """Handle CSP violation reports."""
    
    def __init__(self, log_path: str = "csp_reports.log"):
        self.log_path = log_path
    
    def __call__(self, request: Request) -> Response:
        """Process CSP report."""
        if request.method != "POST":
            return Response.error("Method not allowed", 405)
        
        try:
            if request.json:
                report = request.json
            else:
                report = json.loads(request.body.decode('utf-8'))
            
            self._log_violation(report)
            return Response("", 204)
            
        except json.JSONDecodeError:
            return Response.error("Invalid JSON", 400)
        except Exception as e:
            return Response.error(f"Error processing report: {e}", 500)
    
    def _log_violation(self, report: Dict):
        """Log CSP violation."""
        csp_report = report.get('csp-report', {})
        
        violation = {
            "timestamp": time.time(),
            "document_uri": csp_report.get('document-uri'),
            "referrer": csp_report.get('referrer'),
            "blocked_uri": csp_report.get('blocked-uri'),
            "violated_directive": csp_report.get('violated-directive'),
            "original_policy": csp_report.get('original-policy'),
            "script_sample": csp_report.get('script-sample'),
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(violation) + "\n")


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
        is_secure = (
            request.environ.get("wsgi.url_scheme") == "https" or
            request.environ.get("HTTP_X_FORWARDED_PROTO") == "https"
        )
        
        path = request.environ.get("PATH_INFO", "/")
        # Never redirect admin panel or favicon to HTTPS - the admin UI must work
        # over plain HTTP when the server is not behind an HTTPS terminator.
        skip_redirect = path.startswith('/admin') or path == '/favicon.ico'
        
        if self.enabled and not is_secure and not skip_redirect:
            host = request.environ.get("HTTP_HOST", "localhost")
            query = request.environ.get("QUERY_STRING", "")
            
            https_url = f"https://{host}{path}"
            if query:
                https_url += f"?{query}"
            
            return Response.redirect(https_url, 301)
        
        return handler(request)


# Legacy compatibility
SecurityMiddleware = SecurityHeadersMiddleware
