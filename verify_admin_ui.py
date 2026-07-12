#!/usr/bin/env python3
"""Verify /admin route serves React admin UI."""

import sys
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from webcms.app_factory import create_app


def make_request(app, path, method='GET'):
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
    status_info = {}
    def start_response(status, headers):
        status_info['status'] = status
        status_info['headers'] = dict(headers)
    body = b''.join(app(environ, start_response))
    return status_info, body


def main():
    app = create_app('config_test.json')
    paths = ['/admin', '/admin/', '/admin/index.html', '/admin/assets/main.js', '/admin/dashboard']
    for path in paths:
        status, body = make_request(app, path)
        print(f'{path}: {status["status"]} ({len(body)} bytes)')
        if path in ['/admin', '/admin/', '/admin/index.html']:
            assert '200' in status['status'], f'Expected 200 for {path}'
            assert b'WebCMS Admin' in body or b'admin-shell' in body, f'Expected admin UI content for {path}'


if __name__ == '__main__':
    main()
