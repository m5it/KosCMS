import React, { useEffect, useState } from 'react';

function Dashboard() {
  const [widgets, setWidgets] = useState([]);

  useEffect(() => {
    fetch('/api/v1/admin/dashboard')
      .then((res) => res.json())
      .then((data) => setWidgets(data.widgets || []));
  }, []);

  return (
    <div className="admin-page">
      <h1>Dashboard</h1>
      <div className="widget-grid">
        {widgets.map((widget) => (
          <div key={widget.id} className="widget-card">
            <h3>{widget.icon} {widget.title}</h3>
            <pre>{JSON.stringify(widget.data, null, 2)}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
