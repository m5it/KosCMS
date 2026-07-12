#!/usr/bin/env python3
"""Print the SecurityHeadersMiddleware __call__ method."""

from pathlib import Path

text = Path('webcms/security/middleware.py').read_text()
start = text.find('class SecurityHeadersMiddleware')
print(text[start:start+3500])
