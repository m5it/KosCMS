import React, { useState } from 'react';
import Button from '../components/Button';

function Search() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    author_id: '',
    tags: '',
    date_from: '',
    date_to: ''
  });
  const [results, setResults] = useState([]);
  const [facets, setFacets] = useState({});
  const [suggestions, setSuggestions] = useState([]);

  const handleSearch = async () => {
    const params = new URLSearchParams({ q: query, ...filters });
    const res = await fetch(`/api/v1/search?${params}`);
    const data = await res.json();
    setResults(data.results || []);
    setFacets(data.facets || {});
  };

  const handleSuggest = async (value) => {
    setQuery(value);
    if (value.length < 2) {
      setSuggestions([]);
      return;
    }
    const res = await fetch(`/api/v1/search/suggest?q=${encodeURIComponent(value)}`);
    const data = await res.json();
    setSuggestions(data.suggestions || []);
  };

  const updateFilter = (key, value) => {
    setFilters({ ...filters, [key]: value });
  };

  const applyFacet = (key, value) => {
    if (key === 'tags') {
      const current = filters.tags ? filters.tags.split(',') : [];
      if (!current.includes(value)) {
        updateFilter('tags', [...current, value].join(','));
      }
    } else {
      updateFilter(key, value);
    }
  };

  return (
    <div>
      <h1>Search</h1>
      <input
        type="text"
        value={query}
        onChange={(e) => handleSuggest(e.target.value)}
        placeholder="Search content..."
        style={{ width: '100%', padding: '0.5rem', marginBottom: '0.5rem' }}
      />
      {suggestions.length > 0 && (
        <ul className="card" style={{ listStyle: 'none', padding: '0.5rem' }}>
          {suggestions.map((s) => (
            <li key={s} onClick={() => { setQuery(s); setSuggestions([]); }} style={{ cursor: 'pointer' }}>
              {s}
            </li>
          ))}
        </ul>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.5rem', marginBottom: '1rem' }}>
        <input placeholder="Status" value={filters.status} onChange={(e) => updateFilter('status', e.target.value)} />
        <input placeholder="Author ID" value={filters.author_id} onChange={(e) => updateFilter('author_id', e.target.value)} />
        <input placeholder="Tags" value={filters.tags} onChange={(e) => updateFilter('tags', e.target.value)} />
        <input type="date" value={filters.date_from} onChange={(e) => updateFilter('date_from', e.target.value)} />
        <input type="date" value={filters.date_to} onChange={(e) => updateFilter('date_to', e.target.value)} />
      </div>

      <Button onClick={handleSearch}>Search</Button>

      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '1rem', marginTop: '1rem' }}>
        <div>
          {results.map((item) => (
            <div key={item._id} className="card" style={{ marginBottom: '0.5rem' }}>
              <h4>{item.title}</h4>
              <p dangerouslySetInnerHTML={{ __html: (item.highlight?.content || []).join(' ... ') }} />
            </div>
          ))}
        </div>
        <div className="card">
          <h4>Facets</h4>
          {Object.entries(facets).map(([key, buckets]) => (
            <div key={key}>
              <strong>{key}</strong>
              <ul style={{ listStyle: 'none', padding: 0 }}>
                {buckets.map((bucket) => (
                  <li key={bucket.key}>
                    <button className="btn btn-secondary" onClick={() => applyFacet(key, bucket.key)}>
                      {bucket.key} ({bucket.doc_count})
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Search;
