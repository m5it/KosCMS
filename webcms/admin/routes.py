"""
Admin Routes

Serve the React-based admin UI for /admin and /admin/* paths.
"""

import mimetypes
from pathlib import Path
from webcms.core.response import Response


def admin_routes(app):
    """Register admin routes serving the built React admin UI."""
    dist_dir = Path(__file__).parent.parent / 'admin-ui' / 'dist'
    index_path = dist_dir / 'index.html'

    def _serve_file(path):
        if not path.exists() or not path.is_file():
            return None
        content_type = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        with open(path, 'rb') as f:
            body = f.read()
        return Response(body, 200, headers={'Content-Type': content_type})

    @app.route('/admin', methods=['GET'])
    @app.route('/admin/', methods=['GET'])
    def admin_index(request):
        if not index_path.exists():
            return Response.html('<p>Admin UI not built. Run <code>npm run build</code> in webcms/admin-ui.</p>', 503)
        return _serve_file(index_path)

    @app.route('/admin/{filename:path}', methods=['GET'])
    def admin_assets(request, filename):
        asset_path = dist_dir / filename
        try:
            asset_path.resolve().relative_to(dist_dir.resolve())
        except ValueError:
            return Response.not_found()
        response = _serve_file(asset_path)
        if response is None:
            return _serve_file(index_path)
        return response
