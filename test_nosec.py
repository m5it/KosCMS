#!/usr/bin/env python3
"""Test server with NO security middleware"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from webcms import Application
from webcms.admin.routes import admin_routes
from webcms.core.response import Response

app = Application('config_nocsp.json')

# Register ONLY admin routes, NO security middleware
admin_routes(app)

@app.route("/", methods=["GET"])
def home(request):
    return Response.redirect("/admin")

print("=" * 60)
print("TEST SERVER - NO SECURITY HEADERS")
print("Running on http://0.0.0.0:9000")
print("=" * 60)
print("\nTry accessing:")
print("  http://192.168.0.68:9000/admin")
print("  http://192.168.0.68:9000/admin/posts")
print("\nIf this works, the issue is security headers (CSP/COEP)")

from wsgiref.simple_server import make_server
server = make_server('0.0.0.0', 9000, app.wsgi_app)
server.serve_forever()
