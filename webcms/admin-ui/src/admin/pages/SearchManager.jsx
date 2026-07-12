import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/search';

function SearchManager() {
  const [analytics, setAnalytics] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [query, setQuery] = useState('');

  useEffect(() => {
    fetchAnalytics();
    fetchSuggestions();
  }, []);

  const fetchAnalytics = async () => {
    const res = await fetch(`${API_BASE}/analytics`);
    const data = await res.json();
    setAnalytics(data);
  };

  const fetchSuggestions = async () => {
    const res = await fetch(`${API_BASE}/suggestions`);
    const data = await res.json();
    setSuggestions(data.suggestions || []);
  };

  const addSuggestion = async () => {
    if (!query.trim()) return;
    await fetch(`${API_BASE}/suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    setQuery('');
    fetchSuggestions();
  };

  const removeSuggestion = async (id) => {
    await fetch(`${API_BASE}/suggestions/${id}`, { method: 'DELETE' });
    fetchSuggestions();
  };

  return (
    <div className="admin-page">
      <h1>Search</h1>
      {analytics && (
        <div className="dashboard-grid">
          <div className="card"><h3>Queries 24h</h3><p>{analytics.queries_24h}</p></div>
          <div className="card"><h3>Top Query</h3><p>{analytics.top_query || '—'}</p></div>
          <div className="card"><h3>No Results</h3><p>{analytics.no_results_rate}%</p></div>
          <div className="card"><h3>Avg Time</h3><p>{analytics.avg_time_ms}ms</p></div>
        </div>
      )}
      <div className="settings-group" style={{ marginTop: '1.5rem' }}>
        <h3>Suggestions</h3>
        <div className="form-actions">
          <input
            type="text"
            placeholder="Add suggestion query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn" onClick={addSuggestion}>Add</button>
        </div>
        {suggestions.map((s) => (
          <div key={s.id} className="plugin-row">
            <span>{s.query}</span>
            <button className="btn btn-secondary" onClick={() => removeSuggestion(s.id)}>Remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SearchManager;
