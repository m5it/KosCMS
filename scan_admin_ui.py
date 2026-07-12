#!/usr/bin/env python3
"""Scan admin UI files for common JSX/JS issues."""

import re
from pathlib import Path

ROOT = Path('webcms/admin-ui/src/admin')

issues = []

for path in ROOT.rglob('*.jsx'):
    text = path.read_text()
    rel = path.relative_to(ROOT)

    # Literal \n in JSX/JS source (corrupted file)
    if r'\n' in text and '\\\\n' not in text:
        # Check if it's actually a literal newline escape in a string
        pass  # skip false positives

    # Corrupted escaped newlines as separate characters
    if '\\n' in text:
        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if line.endswith('\\') and 'n' in line:
                issues.append(f'{rel}:{i}: possible corrupted newline escape')

    # Find literal escaped quotes that shouldn't be in JSX
    if '\\"' in text or "\\'" in text:
        issues.append(f'{rel}: contains escaped quotes (possible corruption)')

    # Check for balanced braces in JSX-ish content
    open_brace = text.count('{')
    close_brace = text.count('}')
    if open_brace != close_brace:
        issues.append(f'{rel}: unbalanced braces ({open_brace} open, {close_brace} close)')

    # Check for balanced JSX tags roughly
    tags = re.findall(r'<([A-Za-z][A-Za-z0-9]*)[^>]*>', text)
    close_tags = re.findall(r'</([A-Za-z][A-Za-z0-9]*)>', text)
    # Not a strict check, just flag obvious mismatches
    if len(tags) < len(close_tags):
        issues.append(f'{rel}: more closing JSX tags than opening tags')

    # Check imports exist for referenced components
    imports = re.findall(r"import\s+(\w+)\s+from", text)
    used = set(re.findall(r'<(\w+)', text))
    for comp in used:
        if comp not in imports and comp not in ['div', 'span', 'h1', 'h2', 'h3', 'h4', 'p', 'small', 'nav', 'aside', 'header', 'main', 'ul', 'li', 'table', 'thead', 'tbody', 'tr', 'td', 'th', 'button', 'input', 'select', 'option', 'textarea', 'label', 'code', 'pre', 'strong', 'img', 'a', 'form']:
            issues.append(f'{rel}: uses <{comp}> but it is not imported')

for issue in issues:
    print(issue)

if not issues:
    print('No obvious issues found.')
