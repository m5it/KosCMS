import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';
import ContentEditor from '../components/ContentEditor';

const API_BASE = '/api/v1/admin';

function ContentManager() {
  const [activeTab, setActiveTab] = useState('posts');
  const [items, setItems] = useState([]);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    fetchItems();
  }, [activeTab]);

  const fetchItems = async () => {
    const res = await fetch(`${API_BASE}/${activeTab}`);
    const data = await res.json();
    setItems(data[activeTab] || []);
  };

  const handleSave = async (form) => {
    const url = form.id ? `${API_BASE}/${activeTab}/${form.id}` : `${API_BASE}/${activeTab}`;
    const method = form.id ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    });
    if (res.ok) {
      setEditing(null);
      fetchItems();
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete ${row.title}?`)) return;
    const res = await fetch(`${API_BASE}/${activeTab}/${row.id}`, { method: 'DELETE' });
    if (res.ok) fetchItems();
  };

  const columns = [
    { key: 'title', label: 'Title' },
    { key: 'slug', label: 'Slug' },
    { key: 'status', label: 'Status' },
    { key: 'author', label: 'Author' },
    { key: 'updated_at', label: 'Updated' }
  ];

  return (
    <div className="admin-page">
      <h1>Pages & Posts</h1>

      <div className="tabs">
        <button className={activeTab === 'posts' ? 'active' : ''} onClick={() => { setActiveTab('posts'); setEditing(null); }}>Posts</button>
        <button className={activeTab === 'pages' ? 'active' : ''} onClick={() => { setActiveTab('pages'); setEditing(null); }}>Pages</button>
      </div>

      {editing ? (
        <ContentEditor
          item={editing}
          type={activeTab === 'posts' ? 'Post' : 'Page'}
          onSave={handleSave}
          onCancel={() => setEditing(null)}
        />
      ) : (
        <>
          <button className="btn" onClick={() => setEditing({})}>New {activeTab === 'posts' ? 'Post' : 'Page'}</button>
          <DataTable
            columns={columns}
            rows={items}
            onEdit={setEditing}
            onDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
}

export default ContentManager;
