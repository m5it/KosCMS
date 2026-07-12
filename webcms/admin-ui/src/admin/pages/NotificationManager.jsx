import React, { useEffect, useState } from 'react';

const API_BASE = '/api/v1/admin/notifications';

function NotificationManager() {
  const [preferences, setPreferences] = useState({});
  const [recipients, setRecipients] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [queue, setQueue] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchPreferences();
    fetchQueue();
  }, []);

  const fetchPreferences = async () => {
    const res = await fetch(`${API_BASE}/preferences`);
    const data = await res.json();
    setPreferences(data.preferences || {});
  };

  const fetchQueue = async () => {
    const res = await fetch(`${API_BASE}/queue`);
    const data = await res.json();
    setQueue(data);
  };

  const savePreferences = async () => {
    await fetch(`${API_BASE}/preferences`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(preferences)
    });
    setMessage('Preferences saved');
  };

  const send = async () => {
    const res = await fetch(`${API_BASE}/send`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipients: recipients.split(',').map((s) => s.trim()), subject, body })
    });
    const data = await res.json();
    setMessage(`Sent ${data.sent || 0} notifications`);
    fetchQueue();
  };

  const triggerDigest = async () => {
    const res = await fetch(`${API_BASE}/digest`, { method: 'POST' });
    const data = await res.json();
    setMessage(`Digest triggered: ${data.scheduled || 0} queued`);
    fetchQueue();
  };

  const updatePref = (key, value) => setPreferences({ ...preferences, [key]: value });

  return (
    <div className="admin-page">
      <h1>Notifications</h1>
      {message && <div className="alert">{message}</div>}

      <div className="settings-group">
        <h3>Preferences</h3>
        <div className="form-grid">
          <label>Email Enabled</label>
          <input type="checkbox" checked={preferences.email_enabled || false} onChange={(e) => updatePref('email_enabled', e.target.checked)} />
          <label>Digest Enabled</label>
          <input type="checkbox" checked={preferences.digest_enabled || false} onChange={(e) => updatePref('digest_enabled', e.target.checked)} />
          <label>Digest Frequency</label>
          <select value={preferences.digest_frequency || 'daily'} onChange={(e) => updatePref('digest_frequency', e.target.value)}>
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
          </select>
        </div>
        <div className="form-actions">
          <button className="btn" onClick={savePreferences}>Save Preferences</button>
        </div>
      </div>

      <div className="settings-group">
        <h3>Manual Send</h3>
        <div className="form-grid">
          <label>Recipients (comma separated)</label>
          <input type="text" value={recipients} onChange={(e) => setRecipients(e.target.value)} />
          <label>Subject</label>
          <input type="text" value={subject} onChange={(e) => setSubject(e.target.value)} />
          <label>Body</label>
          <textarea rows={4} value={body} onChange={(e) => setBody(e.target.value)} />
        </div>
        <div className="form-actions">
          <button className="btn" onClick={send}>Send</button>
          <button className="btn btn-secondary" onClick={triggerDigest}>Trigger Digest</button>
        </div>
      </div>

      {queue && (
        <div className="settings-group">
          <h3>Email Queue</h3>
          <div className="dashboard-grid">
            <div className="card"><h3>Pending</h3><p>{queue.pending}</p></div>
            <div className="card"><h3>Sent 24h</h3><p>{queue.sent_24h}</p></div>
            <div className="card"><h3>Failed</h3><p>{queue.failed}</p></div>
            <div className="card"><h3>Retrying</h3><p>{queue.retrying}</p></div>
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationManager;
