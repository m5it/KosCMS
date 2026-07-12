import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/users';
const ROLES_API = '/api/v1/admin/roles';

function UserManager() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, []);

  const fetchUsers = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setUsers(data.users || []);
  };

  const fetchRoles = async () => {
    const res = await fetch(ROLES_API);
    const data = await res.json();
    setRoles(data.roles || []);
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
      fetchUsers();
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete ${row.username}?`)) return;
    await fetch(`${API_BASE}/${row.id}`, { method: 'DELETE' });
    fetchUsers();
  };

  const toggleActive = async (row) => {
    await fetch(`${API_BASE}/${row.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...row, is_active: !row.is_active })
    });
    fetchUsers();
  };

  const columns = [
    { key: 'username', label: 'Username' },
    { key: 'email', label: 'Email' },
    { key: 'role', label: 'Role' },
    { key: 'is_active', label: 'Active' }
  ];

  return (
    <div className="admin-page">
      <h1>Users</h1>

      {editing ? (
        <div className="content-editor">
          <h2>{editing.id ? 'Edit' : 'New'} User</h2>
          <div className="form-grid">
            <label>Username</label>
            <input value={editing.username || ''} onChange={(e) => setEditing({ ...editing, username: e.target.value })} />
            <label>Email</label>
            <input value={editing.email || ''} onChange={(e) => setEditing({ ...editing, email: e.target.value })} />
            <label>Role</label>
            <select value={editing.role || ''} onChange={(e) => setEditing({ ...editing, role: e.target.value })}>
              <option value="">Select role</option>
              {roles.map((r) => (
                <option key={r.id} value={r.name}>{r.name}</option>
              ))}
            </select>
            <label>Active</label>
            <input
              type="checkbox"
              checked={editing.is_active || false}
              onChange={(e) => setEditing({ ...editing, is_active: e.target.checked })}
            />
          </div>
          <div className="form-actions">
            <button className="btn" onClick={handleSave}>Save</button>
            <button className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </div>
      ) : (
        <>
          <button className="btn" onClick={() => setEditing({ is_active: true })}>New User</button>
          <DataTable
            columns={columns}
            rows={users}
            onEdit={setEditing}
            onDelete={handleDelete}
          />
          <div style={{ marginTop: '1rem' }}>
            {users.map((u) => (
              <div key={u.id} className="plugin-row">
                <span>{u.username} ({u.email})</span>
                <button className="btn btn-secondary" onClick={() => toggleActive(u)}>
                  {u.is_active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

export default UserManager;
