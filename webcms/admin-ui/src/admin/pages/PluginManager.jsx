import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/plugins';

function PluginManager() {
  const [plugins, setPlugins] = useState([]);

  useEffect(() => {
    fetchPlugins();
  }, []);

  const fetchPlugins = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setPlugins(data.plugins || []);
  };

  const toggle = async (plugin, active) => {
    const action = active ? 'activate' : 'deactivate';
    await fetch(`${API_BASE}/${plugin.id}/${action}`, { method: 'POST' });
    fetchPlugins();
  };

  const uninstall = async (plugin) => {
    if (!window.confirm(`Uninstall ${plugin.name}?`)) return;
    await fetch(`${API_BASE}/${plugin.id}`, { method: 'DELETE' });
    fetchPlugins();
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'version', label: 'Version' },
    { key: 'active', label: 'Active' }
  ];

  return (
    <div className="admin-page">
      <h1>Plugins</h1>
      <DataTable
        columns={columns}
        rows={plugins}
        onEdit={() => {}}
        onDelete={uninstall}
      />
      <div style={{ marginTop: '1rem' }}>
        {plugins.map((p) => (
          <div key={p.id} className="plugin-row">
            <strong>{p.name}</strong>
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
