import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/backups';

function BackupManager() {
  const [backups, setBackups] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchBackups();
  }, []);

  const fetchBackups = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setBackups(data.backups || []);
  };

  const create = async () => {
    setMessage('Creating backup...');
    const res = await fetch(API_BASE, { method: 'POST' });
    const data = await res.json();
    setMessage(`Backup created: ${data.id}`);
    fetchBackups();
  };

  const restore = async (id) => {
    if (!window.confirm(`Restore backup ${id}?`)) return;
    setMessage('Restoring...');
    const res = await fetch(`${API_BASE}/${id}/restore`, { method: 'POST' });
    const data = await res.json();
    setMessage(data.message || 'Restored');
  };

  const verify = async (id) => {
    const res = await fetch(`${API_BASE}/${id}/verify`, { method: 'POST' });
    const data = await res.json();
    setMessage(`Backup ${id}: ${data.valid ? 'Valid' : 'Invalid'}`);
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete backup ${row.id}?`)) return;
    await fetch(`${API_BASE}/${row.id}`, { method: 'DELETE' });
    fetchBackups();
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'created_at', label: 'Created' },
    { key: 'size', label: 'Size' },
    { key: 'status', label: 'Status' }
  ];

  return (
    <div className="admin-page">
      <h1>Backups</h1>
      {message && <div className="alert">{message}</div>}
      <div className="form-actions">
        <button className="btn" onClick={create}>Create Backup</button>
      </div>
      <DataTable
        columns={columns}
        rows={backups}
        onEdit={() => {}}
        onDelete={handleDelete}
      />
      <div style={{ marginTop: '1rem' }}>
        {backups.map((b) => (
          <div key={b.id} className="plugin-row">
            <span>{b.id} ({b.created_at})</span>
            <div>
              <button className="btn" onClick={() => restore(b.id)}>Restore</button>
              <button className="btn btn-secondary" onClick={() => verify(b.id)}>Verify</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BackupManager;
