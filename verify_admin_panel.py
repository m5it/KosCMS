#!/usr/bin/env python3
"""Verify /admin route serves the admin UI and assets correctly."""

import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from webcms.app_factory import create_app


def request(app, path, method='GET'):
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': '',
        'SERVER_NAME': 'localhost',
        'SERVER_PORT': '8000',
        'HTTP_HOST': 'localhost:8000',
        'wsgi.url_scheme': 'http',
        'wsgi.input': BytesIO(b''),
        'wsgi.errors': sys.stderr,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': True,
    }
    info = {}
    def start_response(status, headers):
        info['status'] = status
        info['headers'] = dict(headers)
    body = b''.join(app(environ, start_response))
    return info, body


def main():
    app = create_app('config_test.json')

    checks = [
        ('/admin', 200, b'/admin/assets/admin.js', 'text/html'),
        ('/admin/', 200, b'sidebar-nav', 'text/html'),
        ('/admin/dashboard', 200, b'sidebar-nav', 'text/html'),
        ('/admin/assets/admin.js', 200, b'const API', 'javascript'),
    ]

    all_ok = True
    for path, expected_status, expected_bytes, content_type in checks:
        info, body = request(app, path)
        status_ok = str(expected_status) in info['status']
        body_ok = expected_bytes in body
        ct_ok = content_type in info['headers'].get('Content-Type', '')
        ok = status_ok and body_ok and ct_ok
        all_ok = all_ok and ok
        print(f'{path}: status={info["status"]} content-type={info["headers"].get("Content-Type")} body_len={len(body)} OK={ok}')

    if all_ok:
        print('\nAll admin panel checks passed.')
    else:
        print('\nSome checks failed.')
        sys.exit(1)


if __name__ == '__main__':
    main()
