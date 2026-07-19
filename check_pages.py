from pathlib import Path

js = Path('webcms/admin-ui/dist/assets/index-CXukPda6.js').read_text()
pages = ['TemplateManager', 'ContentManager', 'Settings', 'PluginManager', 'UserManager', 'RoleManager', 'ThemeManager', 'Dashboard', 'MediaManager', 'CacheManager', 'BackupManager', 'WorkflowManager', 'TenantManager', 'SearchManager', 'NotificationManager']
for p in pages:
    print(f"{p}: {'found' if p in js else 'MISSING'}")
