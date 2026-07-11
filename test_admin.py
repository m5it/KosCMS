#!/usr/bin/env python3
"""Quick test server without middleware"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from webcms import Application
from webcms.admin.routes import admin_routes
from webcms.core.response import Response

app = Application()

# Only admin routes, no middleware
admin_routes(app)

@app.route("/", methods=["GET"])
def home(request):
    return Response.redirect("/admin")

print("Test server running on http://localhost:9000")
print("No middleware, no CSP, just admin routes")

from wsgiref.simple_server import make_server
server = make_server('0.0.0.0', 9000, app.wsgi_app)
server.serve_forever()
