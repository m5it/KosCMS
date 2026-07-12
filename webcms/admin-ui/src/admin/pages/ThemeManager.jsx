import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/themes';

function ThemeManager() {
  const [themes, setThemes] = useState([]);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    fetchThemes();
  }, []);

  const fetchThemes = async () => {
    const res = await fetch(API_BASE);
    const data = await res.json();
    setThemes(data.themes || []);
  };

  const activate = async (id) => {
    await fetch(`${API_BASE}/${id}/activate`, { method: 'POST' });
    fetchThemes();
  };

  return (
    <div className="admin-page">
      <h1>Themes</h1>
      <div className="theme-grid">
        {themes.map((theme) => (
          <div key={theme.id} className={`theme-card ${theme.active ? 'active' : ''}`}>
            <h3>{theme.name}</h3>
            <p>{theme.description}</p>
            <div className="form-actions">
              <button className="btn" onClick={() => activate(theme.id)} disabled={theme.active}>
                {theme.active ? 'Active' : 'Activate'}
              </button>
              <button className="btn btn-secondary" onClick={() => setPreview(theme)}>
                Preview
              </button>
            </div>
          </div>
        ))}
      </div>
      {preview && (
        <div className="theme-preview">
          <h3>Preview: {preview.name}</h3>
          <p>{preview.description}</p>
          <button className="btn btn-secondary" onClick={() => setPreview(null)}>Close</button>
        </div>
      )}
    </div>
  );
}

export default ThemeManager;
