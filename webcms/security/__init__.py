"""
Security Module

Security headers, CSP, CSRF, XSS protection.
"""

from .middleware import (
    SecurityHeadersMiddleware,
    CSPConfig,
    CSPReportHandler,
    NonceGenerator,
    HTTPSRedirectMiddleware
)
from .csrf import CSRFProtection
from .xss import XSSProtection, XSSFilter

# Alias for backward compatibility
SecurityMiddleware = SecurityHeadersMiddleware

__all__ = [
    "SecurityHeadersMiddleware",
    "SecurityMiddleware",  # Alias
    "CSPConfig",
    "CSPReportHandler",
    "NonceGenerator",
    "HTTPSRedirectMiddleware",
    "CSRFProtection",
    "XSSProtection",
    "XSSFilter"
]
