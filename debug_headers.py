#!/usr/bin/env python3
from webcms.core.request import Request
from webcms.core.response import Response
from webcms.security.middleware import SecurityHeadersMiddleware, CSPConfig

class FakeRequest:
    def __init__(self, path):
        self.path = path
        self.id = 'test'

csp = CSPConfig(upgrade_insecure=True)
mw = SecurityHeadersMiddleware(csp_config=csp, hsts_enabled=True)

def handler(request):
    return Response('<html></html>')

for p in ['/admin', '/']:
    req = FakeRequest(p)
    resp = mw(req, handler)
    print(p, dict(resp.headers))
