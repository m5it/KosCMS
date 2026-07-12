import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/tenants';

function TenantManager() {
  const [tenants, setTenants] = useState([]);
  const [editing, setEditing] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setTenants(data.tenants || []);
  };

  const fetchAnalytics = async (id) => {
    const res = await fetch(`${API_BASE}/${id}/analytics`);
    const data = await res.json();
    setAnalytics(data);
  };

  const handleSave = async () => {
    const url = editing.id ? `${API_BASE}/${editing.id}` : API_BASE;
    const method = editing.id ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editing)
    });
    if (res.ok) {
      setEditing(null);
      fetchTenants();
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete tenant ${row.name}?`)) return;
    await fetch(`${API_BASE}/${row.id}`, { method: 'DELETE' });
    fetchTenants();
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'domain', label: 'Domain' },
    { key: 'active', label: 'Active' }
  ];

  return (
    <div className="admin-page">
      <h1>Tenants</h1>
      {editing ? (
        <div className="content-editor">
          <h2>{editing.id ? 'Edit' : 'New'} Tenant</h2>
          <div className="form-grid">
            <label>Name</label>
            <input value={editing.name || ''} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            <label>Domain</label>
            <input value={editing.domain || ''} onChange={(e) => setEditing({ ...editing, domain: e.target.value })} />
            <label>Active</label>
            <input
              type="checkbox"
              checked={editing.active || false}
              onChange={(e) => setEditing({ ...editing, active: e.target.checked })}
            />
          </div>
          <div className="form-actions">
            <button className="btn" onClick={handleSave}>Save</button>
            <button className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <button className="btn" onClick={() => setEditing({ active: true })}>New Tenant</button>
          <DataTable
            columns={columns}
            rows={tenants}
            onEdit={(row) => { setEditing(row); fetchAnalytics(row.id); }}
            onDelete={handleDelete}
          />
        </>
      )}
      {analytics && (
        <div className="settings-group" style={{ marginTop: '1.5rem' }}>
          <h3>Tenant Analytics</h3>
          <div className="dashboard-grid">
            <div className="card"><h3>Users</h3><p>{analytics.users}</p></div>
            <div className="card"><h3>Content</h3><p>{analytics.content_count}</p></div>
            <div className="card"><h3>Storage</h3><p>{analytics.storage}</p></div>
            <div className="card"><h3>Requests</h3><p>{analytics.requests_24h}</p></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TenantManager;
