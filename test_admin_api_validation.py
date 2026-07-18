#!/usr/bin/env python3
"""
Comprehensive validation of admin API endpoints
Tests all endpoints for proper response format and no 500 errors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock KosDB for testing
class MockKosDB:
    def __init__(self):
        self._tables = {}
    
    def list_tables(self):
        return list(self._tables.keys())
    
    def execute(self, sql):
        if "CREATE TABLE" in sql.upper():
            table = sql.split("TABLE")[1].split("(")[0].strip()
            self._tables[table] = []
        return {"success": True}
    
    def query(self, sql):
        return {"rows": []}

def test_endpoint(name, test_func):
    """Test an endpoint and report results"""
    try:
        result = test_func()
        print(f"  ✓ {name}: {result}")
        return True
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

print("=" * 70)
print("Admin API Endpoint Validation")
print("=" * 70)

db = MockKosDB()
results = {"passed": 0, "failed": 0}

# Test 1: Content Manager (Posts/Pages)
print("\n1. Testing ContentManager (Posts/Pages)")
from webcms.content.manager import ContentManager

def test_content():
    cm = ContentManager(db=db)
    posts = cm.list_posts()
    assert isinstance(posts, list), "list_posts should return list"
    pages = cm.list_pages()
    assert isinstance(pages, list), "list_pages should return list"
    return f"{len(posts)} posts, {len(pages)} pages"

if test_endpoint("ContentManager", test_content):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 2: Media Manager
print("\n2. Testing MediaManager")
from webcms.media.manager import MediaManager

def test_media():
    mm = MediaManager(db=db)
    files = mm.list_files()
    assert isinstance(files, list), "list_files should return list"
    return f"{len(files)} files"

if test_endpoint("MediaManager", test_media):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 3: Plugin Manager
print("\n3. Testing PluginManager")
from webcms.plugins.manager import PluginManager

def test_plugins():
    pm = PluginManager(db=db)
    plugins = pm.list_plugins()
    assert isinstance(plugins, list), "list_plugins should return list"
    return f"{len(plugins)} plugins"

if test_endpoint("PluginManager", test_plugins):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 4: User Manager
print("\n4. Testing UserManager")
from webcms.auth.manager import UserManager

def test_users():
    um = UserManager(db=db)
    users = um.list_users()
    assert isinstance(users, list), "list_users should return list"
    roles = um.list_roles()
    assert isinstance(roles, list), "list_roles should return list"
    return f"{len(users)} users, {len(roles)} roles"

if test_endpoint("UserManager", test_users):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 5: Template Engine
print("\n5. Testing TemplateEngine")
from webcms.templates.engine import TemplateEngine

def test_templates():
    te = TemplateEngine(db=db)
    templates = te.list_templates()
    assert isinstance(templates, list), "list_templates should return list"
    return f"{len(templates)} templates"

if test_endpoint("TemplateEngine", test_templates):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 6: Theme Manager
print("\n6. Testing ThemeManager")
from webcms.templates.theme import ThemeManager

def test_themes():
    tm = ThemeManager(db=db)
    themes = tm.list_themes()
    assert isinstance(themes, list), "list_themes should return list"
    return f"{len(themes)} themes"

if test_endpoint("ThemeManager", test_themes):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 7: Workflow Manager
print("\n7. Testing WorkflowManager")
from webcms.workflow.manager import WorkflowManager

def test_workflows():
    wm = WorkflowManager(db=db)
    definitions = wm.list_definitions()
    assert isinstance(definitions, list), "list_definitions should return list"
    instances = wm.list_instances()
    assert isinstance(instances, list), "list_instances should return list"
    return f"{len(definitions)} definitions, {len(instances)} instances"

if test_endpoint("WorkflowManager", test_workflows):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 8: Backup Engine
print("\n8. Testing BackupEngine")
from webcms.backup.engine import BackupEngine

def test_backups():
    be = BackupEngine(db=db, backup_dir="test_backups_val")
    backups = be.list_backups()
    assert isinstance(backups, list), "list_backups should return list"
    return f"{len(backups)} backups"

if test_endpoint("BackupEngine", test_backups):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 9: Cache Manager
print("\n9. Testing CacheManager")
from webcms.cache.manager import CacheManager

def test_cache():
    cm = CacheManager(db=db)
    stats = cm.get_stats()
    assert isinstance(stats, dict), "get_stats should return dict"
    assert "keys" in stats, "stats should have 'keys'"
    return f"{stats['keys']} keys"

if test_endpoint("CacheManager", test_cache):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 10: Tenant Manager
print("\n10. Testing TenantManager")
from webcms.tenants.manager import TenantManager

def test_tenants():
    tm = TenantManager(db=db)
    tenants = tm.list()
    assert isinstance(tenants, list), "list should return list"
    return f"{len(tenants)} tenants"

if test_endpoint("TenantManager", test_tenants):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 11: Search Analytics
print("\n11. Testing SearchAnalytics")
from webcms.search.analytics import SearchAnalytics

def test_search():
    sa = SearchAnalytics(db=db)
    suggestions = sa.list_suggestions()
    assert isinstance(suggestions, list), "list_suggestions should return list"
    stats = sa.get_stats()
    assert isinstance(stats, dict), "get_stats should return dict"
    return f"{len(suggestions)} suggestions"

if test_endpoint("SearchAnalytics", test_search):
    results["passed"] += 1
else:
    results["failed"] += 1

# Test 12: Notification Manager
print("\n12. Testing NotificationManager")
from webcms.notifications.manager import NotificationManager

def test_notifications():
    nm = NotificationManager(db=db)
    stats = nm.get_queue_stats()
    assert isinstance(stats, dict), "get_queue_stats should return dict"
    return f"queue stats available"

if test_endpoint("NotificationManager", test_notifications):
    results["passed"] += 1
else:
    results["failed"] += 1

# Summary
print("\n" + "=" * 70)
print(f"Results: {results['passed']} passed, {results['failed']} failed")
print("=" * 70)

# Cleanup
if os.path.exists("test_backups_val"):
    import shutil
    shutil.rmtree("test_backups_val")

sys.exit(0 if results['failed'] == 0 else 1)
