import React from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import './admin.css';

import Dashboard from './pages/Dashboard';
import ContentManager from './pages/ContentManager';
import MediaManager from './pages/MediaManager';
import PluginManager from './pages/PluginManager';
import TemplateManager from './pages/TemplateManager';
import ThemeManager from './pages/ThemeManager';
import UserManager from './pages/UserManager';
import RoleManager from './pages/RoleManager';
import Settings from './pages/Settings';
import CacheManager from './pages/CacheManager';
import BackupManager from './pages/BackupManager';
import WorkflowManager from './pages/WorkflowManager';
import TenantManager from './pages/TenantManager';
import SearchManager from './pages/SearchManager';
import NotificationManager from './pages/NotificationManager';

const menuGroups = [
  {
    title: 'Content',
    items: [
      { path: 'dashboard', label: 'Dashboard', icon: '📊' },
      { path: 'content', label: 'Pages & Posts', icon: '📝' },
      { path: 'media', label: 'Media', icon: '🖼️' }
    ]
  },
  {
    title: 'Design',
    items: [
      { path: 'templates', label: 'Templates', icon: '📄' },
      { path: 'themes', label: 'Themes', icon: '🎨' },
      { path: 'plugins', label: 'Plugins', icon: '🔌' }
    ]
  },
  {
    title: 'Access',
    items: [
      { path: 'users', label: 'Users', icon: '👤' },
      { path: 'roles', label: 'Roles', icon: '🛡️' },
      { path: 'settings', label: 'Settings', icon: '⚙️' }
    ]
  },
  {
    title: 'Operations',
    items: [
      { path: 'cache', label: 'Cache', icon: '⚡' },
      { path: 'backups', label: 'Backups', icon: '💾' },
      { path: 'workflows', label: 'Workflows', icon: '🔁' },
      { path: 'tenants', label: 'Tenants', icon: '🏢' },
      { path: 'search', label: 'Search', icon: '🔍' },
      { path: 'notifications', label: 'Notifications', icon: '🔔' }
    ]
  }
];

function Breadcrumb() {
  const location = useLocation();
  const parts = location.pathname.split('/').filter(Boolean);
  return (
    <nav className="breadcrumb">
      <Link to="/admin">Admin</Link>
      {parts.slice(1).map((part, index) => (
        <span key={index}> / {part.charAt(0).toUpperCase() + part.slice(1)}</span>
      ))}
    </nav>
  );
}

function Sidebar() {
  const location = useLocation();
  return (
n    <aside className=\"admin-sidebar\">\n      <div className=\"admin-brand\">\n        <h2>WebCMS</h2>\n        <small>Admin Control Panel</small>\n      </div>\n      <nav className=\"admin-nav\">\n        {menuGroups.map((group) => (\n          <div key={group.title} className=\"nav-group\">\n            <h4>{group.title}</h4>\n            <ul>\n              {group.items.map((item) => (\n                <li key={item.path}>\n                  <Link\n                    to={item.path}\n                    className={location.pathname.endsWith(item.path) ? 'active' : ''}\n                  >\n                    <span className=\"nav-icon\">{item.icon}</span>\n                    {item.label}\n                  </Link>\n                </li>\n              ))}\n            </ul>\n          </div>\n        ))}\n      </nav>\n    </aside>\n  );\n}\n\nfunction TopBar() {\n  return (\n    <header className=\"admin-topbar\">\n      <Breadcrumb />\n      <div className=\"admin-profile\">\n        <span>👤 Admin User</span>\n        <button className=\"btn btn-secondary\">Logout</button>\n      </div>\n    </header>\n  );\n}\n\nfunction AdminShell() {\n  return (\n    <div className=\"admin-shell\">\n      <Sidebar />\n      <div className=\"admin-main\">\n        <TopBar />\n        <main className=\"admin-content\">\n          <Routes>\n            <Route path=\"/\" element={<Navigate to=\"dashboard\" replace />} />\n            <Route path=\"dashboard\" element={<Dashboard />} />\n            <Route path=\"content\" element={<ContentManager />} />\n            <Route path=\"media\" element={<MediaManager />} />\n            <Route path=\"plugins\" element={<PluginManager />} />\n            <Route path=\"templates\" element={<TemplateManager />} />\n            <Route path=\"themes\" element={<ThemeManager />} />\n            <Route path=\"users\" element={<UserManager />} />\n            <Route path=\"roles\" element={<RoleManager />} />\n            <Route path=\"settings\" element={<Settings />} />\n            <Route path=\"cache\" element={<CacheManager />} />\n            <Route path=\"backups\" element={<BackupManager />} />\n            <Route path=\"workflows\" element={<WorkflowManager />} />\n            <Route path=\"tenants\" element={<TenantManager />} />\n            <Route path=\"search\" element={<SearchManager />} />\n            <Route path=\"notifications\" element={<NotificationManager />} />\n          </Routes>\n        </main>\n      </div>\n    </div>\n  );\n}\n\nexport default AdminShell;
