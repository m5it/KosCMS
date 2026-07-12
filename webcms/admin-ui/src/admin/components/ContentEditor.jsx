import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

function ContentEditor({ item, type, onSave, onCancel }) {
  const [form, setForm] = useState({
    title: '',
    slug: '',
    content: '',
    status: 'draft',
    published_at: '',
    author_id: '',
    categories: '',
    tags: '',
    ...item
  });

  useEffect(() => {
    if (item) setForm((prev) => ({ ...prev, ...item }));
  }, [item]);

  const update = (key, value) => setForm({ ...form, [key]: value });

  const handleSubmit = (status) => {
    onSave({ ...form, status });
  };

  return (
    <div className="content-editor">
      <h2>{item?.id ? 'Edit' : 'New'} {type}</h2>

      <div className="form-grid">
        <label>Title</label>
        <input value={form.title} onChange={(e) => update('title', e.target.value)} />

        <label>Slug</label>
        <input value={form.slug} onChange={(e) => update('slug', e.target.value)} />

        <label>Status</label>
        <select value={form.status} onChange={(e) => update('status', e.target.value)}>
          <option value="draft">Draft</option>
          <option value="review">Review</option>
          <option value="approved">Approved</option>
          <option value="published">Published</option>
        </select>

        <label>Publish Date</label>
        <input
          type="datetime-local"
          value={form.published_at}
          onChange={(e) => update('published_at', e.target.value)}
        />

        <label>Author</label>
        <select value={form.author_id} onChange={(e) => update('author_id', e.target.value)}>
          <option value="">Select author</option>
          <option value="1">Admin</option>
          <option value="2">Editor</option>
          <option value="3">Author</option>
        </select>

        <label>Categories</label>
        <input value={form.categories} onChange={(e) => update('categories', e.target.value)} placeholder="comma separated" />

        <label>Tags</label>
        <input value={form.tags} onChange={(e) => update('tags', e.target.value)} placeholder="comma separated" />
      </div>

      <div className="editor-split">
        <textarea
          rows={16}
          value={form.content}
          onChange={(e) => update('content', e.target.value)}
          placeholder="Write markdown content..."
        />
        <div className="preview">
          <ReactMarkdown>{form.content || '*Preview*'}</ReactMarkdown>
        </div>
      </div>

      <div className="form-actions">
        <button className="btn" onClick={() => handleSubmit('draft')}>Save Draft</button>
        <button className="btn" onClick={() => handleSubmit('published')}>Publish</button>
        <button className="btn btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  );
}

export default ContentEditor;
