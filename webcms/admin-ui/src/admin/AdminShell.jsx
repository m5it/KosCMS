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
    <aside className="admin-sidebar">
      <div className="admin-brand">
        <h2>WebCMS</h2>
        <small>Admin Control Panel</small>
      </div>
      <nav className="admin-nav">
        {menuGroups.map((group) => (
          <div key={group.title} className="nav-group">
            <h4>{group.title}</h4>
            <ul>
              {group.items.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={location.pathname.endsWith(item.path) ? 'active' : ''}
                  >
                    <span className="nav-icon">{item.icon}</span>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}

function TopBar() {
  return (
    <header className="admin-topbar">
      <Breadcrumb />
      <div className="admin-profile">
        <span>👤 Admin User</span>
        <button className="btn btn-secondary">Logout</button>
      </div>
    </header>
  );
}

function AdminShell() {
  return (
    <div className="admin-shell">
      <Sidebar />
      <div className="admin-main">
        <TopBar />
        <main className="admin-content">
          <Routes>
            <Route path="/" element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="content" element={<ContentManager />} />
            <Route path="media" element={<MediaManager />} />
            <Route path="plugins" element={<PluginManager />} />
            <Route path="templates" element={<TemplateManager />} />
            <Route path="themes" element={<ThemeManager />} />
            <Route path="users" element={<UserManager />} />
            <Route path="roles" element={<RoleManager />} />
            <Route path="settings" element={<Settings />} />
            <Route path="cache" element={<CacheManager />} />
            <Route path="backups" element={<BackupManager />} />
            <Route path="workflows" element={<WorkflowManager />} />
            <Route path="tenants" element={<TenantManager />} />
            <Route path="search" element={<SearchManager />} />
            <Route path="notifications" element={<NotificationManager />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default AdminShell;
