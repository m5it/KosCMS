#!/usr/bin/env python3
"""Fix the test file"""

with open('test_workflows_debug2.py', 'r') as f:
    content = f.read()

content = content.replace(
    'table = sql.split("TABLE")[1].split("(")[0].strip()',
    'table = sql.upper().split("TABLE")[1].split("(")[0].strip()'
)

with open('test_workflows_debug2.py', 'w') as f:
    f.write(content)

print("Fixed")
