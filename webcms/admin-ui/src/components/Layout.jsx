import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

function Layout({ children }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="admin-layout">
      <aside className="sidebar">
        <h2>WebCMS</h2>
        <nav>
          <ul>
            <li><Link to="/">Dashboard</Link></li>
            <li><Link to="/pages/builder">Page Builder</Link></li>
            <li><Link to="/media">Media Gallery</Link></li>
            <li><Link to="/editor">Editor</Link></li>
          </ul>
        </nav>
        <button className="btn" onClick={toggleTheme}>
          {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
        </button>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}

export default Layout;
