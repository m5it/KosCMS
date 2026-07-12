import React, { useState } from 'react';
import Button from '../components/Button';

function MediaGallery() {
  const [items, setItems] = useState([
    { id: 1, name: 'logo.png', selected: false },
    { id: 2, name: 'banner.jpg', selected: false },
    { id: 3, name: 'team.jpg', selected: false }
  ]);

  const toggleSelect = (id) => {
    setItems(items.map((item) =>
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  };

  const selectAll = () => {
    const allSelected = items.every((item) => item.selected);
    setItems(items.map((item) => ({ ...item, selected: !allSelected })));
  };

  const deleteSelected = () => {
    setItems(items.filter((item) => !item.selected));
  };

  const selectedCount = items.filter((item) => item.selected).length;

  return (
    <div>
      <h1>Media Gallery</h1>
      <div style={{ marginBottom: '1rem' }}>
        <Button onClick={selectAll}>Select All</Button>
        <Button variant="secondary" onClick={deleteSelected}>
          Delete Selected ({selectedCount})
        </Button>
      </div>
      <div className="component-library">
        {items.map((item) => (
          <div
            key={item.id}
            className="card"
            onClick={() => toggleSelect(item.id)}
            style={{
              cursor: 'pointer',
              border: item.selected ? '2px solid var(--primary)' : '1px solid var(--border-color)'
            }}
          >
            <input type="checkbox" checked={item.selected} readOnly />
            <p>{item.name}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MediaGallery;
