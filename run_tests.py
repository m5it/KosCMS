#!/usr/bin/env python3
"""Run all available tests and capture results."""

import subprocess
import sys
from pathlib import Path

results = []

# Run pytest on tests/ directory
print('=== Running pytest tests/ ===')
try:
    r = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        capture_output=True, text=True, timeout=120
    )
    print(r.stdout)
    if r.stderr:
        print(r.stderr)
    results.append(('pytest tests/', r.returncode, r.stdout + r.stderr))
except Exception as e:
    results.append(('pytest tests/', -1, str(e)))

# Run standalone test_*.py files
standalone = sorted(Path('.').glob('test_*.py'))
for test_file in standalone:
    print(f'=== Running {test_file} ===')
    try:
        r = subprocess.run(
            [sys.executable, str(test_file)],
            capture_output=True, text=True, timeout=60
        )
        print(r.stdout)
        if r.stderr:
            print(r.stderr)
        results.append((str(test_file), r.returncode, r.stdout + r.stderr))
    except Exception as e:
        results.append((str(test_file), -1, str(e)))

# Summary
print('\n=== SUMMARY ===')
for name, code, output in results:
    status = 'PASS' if code == 0 else 'FAIL' if code > 0 else 'ERROR'
    print(f'{status}: {name}')
