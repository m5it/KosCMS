import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/media';

function MediaManager() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(new Set());

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setItems(data.media || []);
  };

  const toggleSelect = (id) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const selectAll = () => {
    if (selected.size === items.length) setSelected(new Set());
    else setSelected(new Set(items.map((i) => i.id)));
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(API_BASE, { method: 'POST', body: formData });
    if (res.ok) fetchItems();
  };

  const deleteSelected = async () => {
    if (!window.confirm(`Delete ${selected.size} items?`)) return;
    await Promise.all([...selected].map((id) => fetch(`${API_BASE}/${id}`, { method: 'DELETE' })));
    setSelected(new Set());
    fetchItems();
  };

  return (
    <div className="admin-page">
      <h1>Media</h1>
      <div className="toolbar">
        <input type="file" onChange={handleUpload} />
        <button className="btn" onClick={selectAll}>
          {selected.size === items.length ? 'Deselect All' : 'Select All'}
        </button>
        <button className="btn btn-secondary" onClick={deleteSelected} disabled={selected.size === 0}>
          Delete Selected ({selected.size})
        </button>
      </div>
      <div className="media-grid">
        {items.map((item) => (
          <div
            key={item.id}
            className={`media-card ${selected.has(item.id) ? 'selected' : ''}`}
            onClick={() => toggleSelect(item.id)}
          >
            <input type="checkbox" checked={selected.has(item.id)} readOnly />
            <p>{item.name}</p>
            <small>{item.mime_type}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MediaManager;
