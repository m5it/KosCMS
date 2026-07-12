import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import Button from '../components/Button';

function Editor() {
  const [markdown, setMarkdown] = useState('# Hello World\n\nEdit this markdown content.');

  return (
    <div>
      <h1>Rich Text Editor</h1>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <textarea
          value={markdown}
          onChange={(e) => setMarkdown(e.target.value)}
          rows={20}
          style={{ fontFamily: 'monospace', padding: '1rem' }}
        />
        <div className="card" style={{ overflow: 'auto' }}>
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </div>
      </div>
      <Button onClick={() => window.dispatchEvent(new CustomEvent('cms:save'))}>Save</Button>
    </div>
  );
}

export default Editor;
