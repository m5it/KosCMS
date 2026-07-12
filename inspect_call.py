#!/usr/bin/env python3
from pathlib import Path
text = Path('webcms/security/middleware.py').read_text()
start = text.find('def __call__')
print(text[start:start+2500])
