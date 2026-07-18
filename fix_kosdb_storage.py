#!/usr/bin/env python3
"""Fix _is_kosdb method in kosdb_storage.py"""

with open('webcms/workflow/kosdb_storage.py', 'r') as f:
    content = f.read()

old_method = '''    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        cls = getattr(self.db, '__class__', type(self.db))
        cls_name = getattr(cls, '__name__', '')
        return 'KosDB' in cls_name'''

new_method = '''    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        # Check for KosDB by looking for required methods
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open('webcms/workflow/kosdb_storage.py', 'w') as f:
        f.write(content)
    print("Fixed _is_kosdb method")
else:
    print("Could not find the method to replace")
