#!/usr/bin/env python3
"""
Fix duplicate list_users method in admin_api.py
"""

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Find and remove the broken duplicate list_users method
# The broken one is: def list_users(self, request: Request) -> Response:\n            return Response.json({"id": theme_id, "active": False, "error": str(e)}, 400)

broken_pattern = '''    def list_users(self, request: Request) -> Response:
            return Response.json({"id": theme_id, "active": False, "error": str(e)}, 400)

    # ---------------- Users & Roles ----------------

    def list_users(self, request: Request) -> Response:'''

fixed = '''    # ---------------- Users & Roles ----------------

    def list_users(self, request: Request) -> Response:'''

if broken_pattern in content:
    print("Found broken duplicate list_users, fixing...")
    content = content.replace(broken_pattern, fixed)
    
    with open('webcms/admin/admin_api.py', 'w') as f:
        f.write(content)
    print("Fixed duplicate list_users method!")
else:
    print("Pattern not found exactly, trying alternative...")
    
    # Try to find and fix manually
    lines = content.split('\n')
    output_lines = []
    skip_until_proper = False
    found_broken = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for broken list_users pattern
        if 'def list_users(self, request: Request) -> Response:' in line:
            # Look ahead to see if next line has theme_id error
            if i + 1 < len(lines) and 'theme_id' in lines[i + 1]:
                print(f"Found broken list_users at line {i+1}, skipping...")
                found_broken = True
                skip_until_proper = True
                i += 1
                continue
            elif skip_until_proper:
                # This is the proper one, keep it
                print(f"Found proper list_users at line {i+1}, keeping...")
                skip_until_proper = False
                # Add the section header before it
                output_lines.append('    # ---------------- Users & Roles ----------------')
                output_lines.append('')
        
        if not skip_until_proper:
            output_lines.append(line)
        
        i += 1
    
    if found_broken:
        with open('webcms/admin/admin_api.py', 'w') as f:
            f.write('\n'.join(output_lines))
        print("Fixed using line-by-line method!")
    else:
        print("Could not find broken list_users method")
