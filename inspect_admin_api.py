#!/usr/bin/env python3
"""Inspect admin API create_api function."""

from pathlib import Path

text = Path('webcms/admin/api.py').read_text()
start = text.find('def create_api')
if start == -1:
    print('create_api not found')
else:
    print(text[start:start+4000])
