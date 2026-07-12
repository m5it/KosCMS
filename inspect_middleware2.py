#!/usr/bin/env python3
"""Print HTTPSRedirectMiddleware section."""

from pathlib import Path

text = Path('webcms/security/middleware.py').read_text()
start = text.find('class HTTPSRedirectMiddleware')
print(text[start:])
