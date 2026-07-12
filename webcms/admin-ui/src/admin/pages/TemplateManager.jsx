import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/templates';

function TemplateManager() {
  const [templates, setTemplates] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setTemplates(data.templates || []);
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
      fetchTemplates();
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete ${row.name}?`)) return;
    await fetch(`${API_BASE}/${row.id}`, { method: 'DELETE' });
    fetchTemplates();
  };

  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'path', label: 'Path' },
    { key: 'updated_at', label: 'Updated' }
  ];

  return (
    <div className="admin-page">
      <h1>Templates</h1>
      {editing ? (
        <div className="content-editor">
          <h2>{editing.id ? 'Edit' : 'New'} Template</h2>
          <div className="form-grid">
            <label>Name</label>
            <input value={editing.name || ''} onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            <label>Path</label>
            <input value={editing.path || ''} onChange={(e) => setEditing({ ...editing, path: e.target.value })} />
            <label>Content</label>
            <textarea
              rows={12}
              value={editing.content || ''}
              onChange={(e) => setEditing({ ...editing, content: e.target.value })}
            />
          </div>
          <div className="form-actions">
            <button className="btn" onClick={handleSave}>Save</button>
            <button className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <button className="btn" onClick={() => setEditing({})}>New Template</button>
          <DataTable
            columns={columns}
            rows={templates}
            onEdit={setEditing}
            onDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
}

export default TemplateManager;
