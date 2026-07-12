import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const API_BASE = '/api/v1/admin/roles';

const ALL_PERMISSIONS = [
  'content:read', 'content:write', 'content:delete',
  'media:read', 'media:write', 'media:delete',
  'plugins:manage',
  'users:manage', 'roles:manage',
  'settings:manage',
  'cache:manage',
  'backups:manage',
  'workflows:manage',
  'tenants:manage',
  'notifications:send'
];

function RoleManager() {
  const [roles, setRoles] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetchRoles();
  }, []);

  const fetchRoles = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setRoles(data.roles || []);
  };

  const handleSave = async () => {
    const res = await fetch(`${API_BASE}/${editing.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editing)
    });
    if (res.ok) {
      setEditing(null);
      fetchRoles();
    }
  };

  const togglePermission = (perm) => {
    const perms = new Set(editing.permissions || []);
    if (perms.has(perm)) perms.delete(perm);
    else perms.add(perm);
    setEditing({ ...editing, permissions: [...perms] });
  };

  const columns = [
    { key: 'name', label: 'Role' },
    { key: 'permissions', label: 'Permissions' }
  ];

  return (
    <div className="admin-page">
      <h1>Roles & Permissions</h1>
      {editing ? (
        <div className="content-editor">
          <h2>Edit {editing.name}</h2>
          <div className="permission-grid">
            {ALL_PERMISSIONS.map((perm) => (
              <label key={perm} className="permission-item">
                <input
                  type="checkbox"
                  checked={(editing.permissions || []).includes(perm)}
                  onChange={() => togglePermission(perm)}
                />
                {perm}
              </label>
            ))}
          </div>
          <div className="form-actions">
            <button className="btn" onClick={handleSave}>Save</button>
            <button className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </div>
      ) : (
        <DataTable
          columns={columns}
          rows={roles}
          onEdit={setEditing}
          onDelete={() => {}}
        />
      )}
    </div>
  );
}

export default RoleManager;
