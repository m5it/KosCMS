#!/usr/bin/env python3
"""
Fix duplicate list_users method in admin_api.py
"""

import re

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Find the duplicate list_users method
# The pattern shows there's a broken method that returns theme_id response
# followed by a proper list_users method

# Find the broken duplicate (the one that returns theme_id response)
broken_pattern = r'    def list_users\\(self, request: Request\\) -> Response:\\s+return Response\\.json\\(\\{"id": theme_id, "active": False, "error": str\\(e\\)\\}, 400\\)\\s+\\n    # ---------------- Users & Roles ----------------\\s+\\n    def list_users\\(self, request: Request\\) -> Response:'

# Replace with just the comment and the proper method
replacement = '''    # ---------------- Users & Roles ----------------

    def list_users(self, request: Request) -> Response:'''

# Check if pattern exists
if re.search(broken_pattern, content):
    print("Found broken duplicate list_users, fixing...")
    content = re.sub(broken_pattern, replacement, content)
    
    with open('webcms/admin/admin_api.py', 'w') as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found, checking for other duplicates...")
    
    # Count occurrences of list_users definition
    count = content.count('def list_users(self, request: Request) -> Response:')
    print(f"Found {count} list_users method definitions")
    
    if count > 1:
        # Find all occurrences
        lines = content.split('\\n')
        line_numbers = []
        for i, line in enumerate(lines):
            if 'def list_users(self, request: Request) -> Response:' in line:
                line_numbers.append(i)
        
        print(f"list_users definitions at lines: {[n+1 for n in line_numbers]}")
        
        # Show context around each
        for num in line_numbers:
            print(f"\\n--- Around line {num+1} ---")
            for j in range(max(0, num-2), min(len(lines), num+5)):
                print(f"{j+1}: {lines[j]}")
