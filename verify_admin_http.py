#!/usr/bin/env python3
"""Verify admin middleware does not force HTTPS/HSTS for /admin and /favicon.ico."""

import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from webcms.core.request import Request
from webcms.core.response import Response
from webcms.security.middleware import SecurityHeadersMiddleware, HTTPSRedirectMiddleware, CSPConfig


class FakeRequest:
    def __init__(self, path, secure=False):
        self.path = path
        self.environ = {
            'PATH_INFO': path,
            'wsgi.url_scheme': 'https' if secure else 'http',
            'HTTP_HOST': 'aiiaframework.com:8000',
        }
        self.id = 'test'


def test_security_middleware():
    csp = CSPConfig(upgrade_insecure=True)
    mw = SecurityHeadersMiddleware(csp_config=csp, hsts_enabled=True)
    
    def admin_handler(request):
        resp = Response('<html></html>')
        resp.headers['Content-Security-Policy'] = "script-src 'self';"
        return resp
    
    req = FakeRequest('/admin')
    resp = mw(req, admin_handler)
    
    csp_header = resp.headers.get('Content-Security-Policy', '')
    hsts_header = resp.headers.get('Strict-Transport-Security')
    
    assert "upgrade-insecure-requests" not in csp_header, f'Admin CSP should not upgrade: {csp_header}'
    assert hsts_header is None, f'Admin should not get HSTS: {hsts_header}'
    print('PASS: SecurityHeadersMiddleware skips HSTS and preserves admin CSP')
    
    def public_handler(request):
        return Response('<html></html>')
    
    req = FakeRequest('/')
    resp = mw(req, public_handler)
    hsts_header = resp.headers.get('Strict-Transport-Security')
    assert hsts_header is not None, 'Public pages should still get HSTS'
    print('PASS: SecurityHeadersMiddleware still sets HSTS for public pages')


def test_https_redirect():
    mw = HTTPSRedirectMiddleware(enabled=True)
    
    def handler(request):
        return Response('ok')
    
    for path in ['/admin', '/admin/assets/admin.js', '/favicon.ico']:
        req = FakeRequest(path)
        resp = mw(req, handler)
        assert resp.status == 200, f'{path} should not redirect, got {resp.status}'
        assert 'Location' not in resp.headers, f'{path} got Location header'
        print(f'PASS: HTTPSRedirectMiddleware skips {path}')
    
    req = FakeRequest('/some-public-page')
    resp = mw(req, handler)
    assert resp.status == 301, 'Public pages should still redirect to HTTPS'
    print('PASS: HTTPSRedirectMiddleware still redirects public pages')


if __name__ == '__main__':
    test_security_middleware()
    test_https_redirect()
    print('\nAll middleware checks passed.')
