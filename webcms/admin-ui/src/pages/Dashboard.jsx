import React from 'react';
import Card from '../components/Card';

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <div className="component-library">
        <Card title="Content">
          <p>12 posts, 4 pages</p>
        </Card>
        <Card title="Media">
          <p>48 files</p>
        </Card>
        <Card title="Workflows">
          <p>3 pending reviews</p>
        </Card>
        <Card title="Cache">
          <p>92% hit rate</p>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
