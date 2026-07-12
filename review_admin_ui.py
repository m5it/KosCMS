#!/usr/bin/env python3
"""Comprehensive review of admin UI files."""

import re
from pathlib import Path

ROOT = Path('webcms/admin-ui/src/admin')
findings = []

for path in ROOT.rglob('*.jsx'):
    text = path.read_text()
    rel = str(path.relative_to(ROOT))

    # Check for corrupted literal escapes (from broken WriteFile behavior)
    if '\\n' in text or '\\"' in text or "\\'" in text:
        findings.append(f'{rel}: contains literal escaped characters (possible corruption)')

    # Check for common JSX issues
    if text.count('(') != text.count(')'):
        findings.append(f'{rel}: unbalanced parentheses')

    # Check API endpoint consistency
    api_calls = re.findall(r"fetch\(`?(/api/v1/admin[^`']*)`?", text)
    api_calls += re.findall(r"API(_BASE)?\s*=\s*['\"](/api/v1/admin[^'\"]*)['\"]", text)
    for call in api_calls:
        if isinstance(call, tuple):
            call = call[-1]
        if not call.startswith('/api/v1/admin'):
            findings.append(f'{rel}: suspicious API call {call}')

    # Check for undefined handlers
    for match in re.finditer(r"onClick=\{(\w+)\}", text):
        fn = match.group(1)
        if fn not in text:
            findings.append(f'{rel}: onClick handler {fn} not defined in file')

for path in ROOT.rglob('*.css'):
    text = path.read_text()
    if '{' in text:
        if text.count('{') != text.count('}'):
            findings.append(f'{path.relative_to(ROOT)}: unbalanced CSS braces')

for finding in findings:
    print(finding)

if not findings:
    print('No critical issues found in admin UI files.')
else:
    print(f'\nTotal findings: {len(findings)}')
