"""
No-Security Middleware - for testing only
"""

class NoSecurityMiddleware:
    """Middleware that strips all security headers."""
    
    def __init__(self):
        pass
    
    def __call__(self, request, handler):
        response = handler(request)
        # Clear all security headers that might cause issues
        headers_to_remove = [
            'Content-Security-Policy',
            'Content-Security-Policy-Report-Only',
            'Cross-Origin-Embedder-Policy',
            'Cross-Origin-Opener-Policy',
            'Cross-Origin-Resource-Policy',
            'Strict-Transport-Security',
            'X-Frame-Options',
        ]
        for h in headers_to_remove:
            response.headers.pop(h, None)
        return response
