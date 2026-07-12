import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/cache';

function CacheManager() {
  const [stats, setStats] = useState(null);
  const [patterns, setPatterns] = useState(['page:*', 'fragment:*', 'api:*']);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    setStats(data);
  };

  const invalidate = async (pattern) => {
    const res = await fetch(`${API_BASE}/invalidate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pattern })
    });
    const data = await res.json();
    setMessage(`Invalidated ${data.deleted || 0} keys matching ${pattern}`);
    fetchStats();
  };

  const warm = async () => {
    const res = await fetch(`${API_BASE}/warm`, { method: 'POST' });
    const data = await res.json();
    setMessage(`Warmed ${data.warmed || 0} cache entries`);
    fetchStats();
  };

  return (
    <div className="admin-page">
      <h1>Cache</h1>
      {message && <div className="alert">{message}</div>}
      {stats && (
        <div className="dashboard-grid">
          <div className="card"><h3>Keys</h3><p>{stats.keys}</p></div>
          <div className="card"><h3>Hit Rate</h3><p>{stats.hit_rate}%</p></div>
          <div className="card"><h3>Memory</h3><p>{stats.memory}</p></div>
          <div className="card"><h3>Evicted</h3><p>{stats.evicted}</p></div>
        </div>
      )}
      <div className="settings-group" style={{ marginTop: '1.5rem' }}>
        <h3>Warm Cache</h3>
        <button className="btn" onClick={warm}>Warm Popular Pages</button>
      </div>
      <div className="settings-group">
        <h3>Invalidate by Pattern</h3>
        {patterns.map((pattern) => (
          <div key={pattern} className="plugin-row">
            <code>{pattern}</code>
            <button className="btn btn-secondary" onClick={() => invalidate(pattern)}>Invalidate</button>
          </div>
        ))}
        <div className="form-actions">
          <button className="btn btn-secondary" onClick={() => invalidate('*')}>Flush All</button>
        </div>
      </div>
    </div>
  );
}

export default CacheManager;
