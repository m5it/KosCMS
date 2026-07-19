import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/plugins';

function PluginManager() {
  const [plugins, setPlugins] = useState([]);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState(null);
  const [installName, setInstallName] = useState('');

  const fetchPlugins = async () => {
    setError(null);
    try {
      const res = await fetch(API_BASE);
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      setPlugins(data.plugins || []);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    fetchPlugins();
  }, []);

  const showMessage = (text) => {
    setMessage(text);
    setTimeout(() => setMessage(null), 4000);
  };

  const toggle = async (plugin, active) => {
    const action = active ? 'activate' : 'deactivate';
    try {
      const res = await fetch(`${API_BASE}/${plugin.id}/${action}`, { method: 'POST' });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Action failed');
      showMessage(data.message);
      fetchPlugins();
    } catch (e) {
      setError(e.message);
    }
  };

  const uninstall = async (plugin) => {
    if (!window.confirm(`Uninstall ${plugin.name}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/${plugin.id}`, { method: 'DELETE' });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Uninstall failed');
      showMessage(data.message);
      fetchPlugins();
    } catch (e) {
      setError(e.message);
    }
  };

  const installByName = async () => {
    if (!installName.trim()) return;
    try {
      const res = await fetch(API_BASE, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: installName.trim() })
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Install failed');
      showMessage(data.message);
      setInstallName('');
      fetchPlugins();
    } catch (e) {
      setError(e.message);
    }
  };

  const uploadFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('plugin', file);
    try {
      const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!data.success) throw new Error(data.message || 'Upload failed');
      showMessage(data.message);
      e.target.value = '';
      fetchPlugins();
    } catch (err) {
      setError(err.message);
    }
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'version', label: 'Version' },
    { key: 'author', label: 'Author' },
    { key: 'active', label: 'Active' },
    { key: 'installed', label: 'Installed' }
  ];

  return (
    <div className="admin-page">
      <h1>Plugins</h1>
      {error && <div className="error-box">{error}</div>}
      {message && <div className="success-box">{message}</div>}
      <div className="toolbar" style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Plugin name to install"
          value={installName}
          onChange={(e) => setInstallName(e.target.value)}
        />
        <button className="btn" onClick={installByName}>Install</button>
        <label className="btn" style={{ cursor: 'pointer' }}>
          Upload Plugin
          <input type="file" accept=".zip" style={{ display: 'none' }} onChange={uploadFile} />
        </label>
      </div>
      <DataTable
        columns={columns}
        rows={plugins}
        onEdit={() => {}}
        onDelete={uninstall}
      />
      <div style={{ marginTop: '1rem' }}>
        {plugins.map((p) => (
          <div key={p.id} className="plugin-row" style={{ marginBottom: '1rem', padding: '0.75rem', border: '1px solid #ddd' }}>
            <div><strong>{p.name}</strong> <span className="badge">{p.version}</span></div>
            <div className="meta" style={{ color: '#666', fontSize: '0.9rem' }}>
              by {p.author || 'Unknown'} {p.min_cms_version && `• CMS ${p.min_cms_version}+`}
            </div>
            <p>{p.description}</p>
            <button className="btn" onClick={() => toggle(p, !p.active)}>
              {p.active ? 'Deactivate' : 'Activate'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PluginManager;
