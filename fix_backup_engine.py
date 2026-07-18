#!/usr/bin/env python3
"""Fix backup engine return format"""

with open('webcms/backup/engine.py', 'r') as f:
    content = f.read()

# Fix the create_backup return to use 'id' key
content = content.replace(
    '"backup_id": backup_id,',
    '"id": backup_id,'
)

# Fix the reference in create_backup
content = content.replace(
    'return backup_data',
    '''# Ensure id key exists
        if "id" not in backup_data:
            backup_data["id"] = backup_data.get("backup_id")
        return backup_data'''
)

with open('webcms/backup/engine.py', 'w') as f:
    f.write(content)

print("Fixed backup engine")
