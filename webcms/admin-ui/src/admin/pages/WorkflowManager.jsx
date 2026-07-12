import React, { useEffect, useState } from 'react';
import DataTable from '../components/DataTable';

const INSTANCES_API = '/api/v1/admin/workflows/instances';
const DEFINITIONS_API = '/api/v1/admin/workflows/definitions';

function WorkflowManager() {
  const [instances, setInstances] = useState([]);
  const [definitions, setDefinitions] = useState([]);
  const [reviewers, setReviewers] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchInstances();
    fetchDefinitions();
    fetchReviewers();
  }, []);

  const fetchInstances = async () => {
    const res = await fetch(INSTANCES_API);
    const data = await res.json();
    setInstances(data.instances || []);
  };

  const fetchDefinitions = async () => {
    const res = await fetch(DEFINITIONS_API);
    const data = await res.json();
    setDefinitions(data.definitions || []);
  };

  const fetchReviewers = async () => {
    const res = await fetch('/api/v1/admin/users?role=editor');
    const data = await res.json();
    setReviewers(data.users || []);
  };

  const transition = async (id, action) => {
    const res = await fetch(`${INSTANCES_API}/${id}/transition`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    });
    const data = await res.json();
    setMessage(data.message || `Transitioned to ${action}`);
    fetchInstances();
  };

  const assign = async (id, reviewerId) => {
    await fetch(`${INSTANCES_API}/${id}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: reviewerId })
    });
    fetchInstances();
  };

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'content_title', label: 'Content' },
    { key: 'state', label: 'State' },
    { key: 'reviewer', label: 'Reviewer' },
    { key: 'updated_at', label: 'Updated' }
  ];

  return (
    <div className="admin-page">
      <h1>Workflows</h1>
      {message && <div className="alert">{message}</div>}

      <h2>Instances</h2>
      <DataTable
        columns={columns}
        rows={instances}
        onEdit={() => {}}
        onDelete={() => {}}
      />
      <div style={{ marginTop: '1rem' }}>
        {instances.map((inst) => (
          <div key={inst.id} className="workflow-row">
            <div><strong>{inst.content_title}</strong> — <span className="status-badge">{inst.state}</span></div>
            <div className="form-actions">
              {inst.available_actions?.map((action) => (
                <button key={action} className="btn" onClick={() => transition(inst.id, action)}>
                  {action}
                </button>
              ))}
              <select
                value={inst.reviewer_id || ''}
                onChange={(e) => assign(inst.id, e.target.value)}
              >
                <option value="">Assign reviewer</option>
                {reviewers.map((r) => (
                  <option key={r.id} value={r.id}>{r.username}</option>
                ))}
              </select>
            </div>
          </div>
        ))}
      </div>

      <h2 style={{ marginTop: '2rem' }}>Definitions</h2>
      <div className="theme-grid">
        {definitions.map((def) => (
          <div key={def.id} className="theme-card">
            <h3>{def.name}</h3>
            <p>{def.description}</p>
            <small>States: {def.states?.join(', ')}</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default WorkflowManager;
