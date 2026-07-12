import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/settings';

function Settings() {
  const [settings, setSettings] = useState({
    site_name: 'WebCMS',
    site_url: 'https://example.com',
    admin_email: 'admin@example.com',
    default_language: 'en',
    posts_per_page: 10,
    cache_enabled: true,
    cache_ttl: 300,
    search_enabled: true,
    elasticsearch_url: 'http://localhost:9200',
    notifications_enabled: true,
    smtp_host: 'localhost',
    smtp_port: 587,
    smtp_user: '',
    smtp_pass: '',
    csp_enabled: true,
    require_https: false
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setSettings((prev) => ({ ...prev, ...data.settings }));
  };

  const handleSave = async () => {
    await fetch(API_BASE, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
  };

  const update = (key, value) => setSettings({ ...settings, [key]: value });

  const groups = [
    {
      title: 'Site',
      fields: [
        { key: 'site_name', label: 'Site Name', type: 'text' },
        { key: 'site_url', label: 'Site URL', type: 'text' },
        { key: 'admin_email', label: 'Admin Email', type: 'email' },
        { key: 'default_language', label: 'Default Language', type: 'text' },
        { key: 'posts_per_page', label: 'Posts Per Page', type: 'number' }
      ]
    },
    {
      title: 'Cache',
      fields: [
        { key: 'cache_enabled', label: 'Cache Enabled', type: 'checkbox' },
        { key: 'cache_ttl', label: 'Cache TTL (seconds)', type: 'number' }
      ]
    },
    {
      title: 'Search',
      fields: [
        { key: 'search_enabled', label: 'Search Enabled', type: 'checkbox' },
        { key: 'elasticsearch_url', label: 'Elasticsearch URL', type: 'text' }
      ]
    },
    {
      title: 'Notifications',
      fields: [
        { key: 'notifications_enabled', label: 'Notifications Enabled', type: 'checkbox' },
        { key: 'smtp_host', label: 'SMTP Host', type: 'text' },
        { key: 'smtp_port', label: 'SMTP Port', type: 'number' },
        { key: 'smtp_user', label: 'SMTP User', type: 'text' },
        { key: 'smtp_pass', label: 'SMTP Password', type: 'password' }
      ]
    },
    {
      title: 'Security',
      fields: [
        { key: 'csp_enabled', label: 'CSP Enabled', type: 'checkbox' },
        { key: 'require_https', label: 'Require HTTPS', type: 'checkbox' }
      ]
    }
  ];

  return (
    <div className="admin-page">
      <h1>Settings</h1>
      {groups.map((group) => (
        <div key={group.title} className="settings-group">
          <h3>{group.title}</h3>
          <div className="form-grid">
            {group.fields.map((field) => (
              <React.Fragment key={field.key}>
                <label>{field.label}</label>
                {field.type === 'checkbox' ? (
                  <input
                    type="checkbox"
                    checked={settings[field.key] || false}
                    onChange={(e) => update(field.key, e.target.checked)}
                  />
                ) : (
                  <input
                    type={field.type}
                    value={settings[field.key] || ''}
                    onChange={(e) => update(field.key, e.target.value)}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      ))}
      <div className="form-actions">
        <button className="btn" onClick={handleSave}>Save Settings</button>
      </div>
    </div>
  );
}

export default Settings;
