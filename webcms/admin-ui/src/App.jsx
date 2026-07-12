import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ShortcutsProvider } from './context/ShortcutsContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import PageBuilder from './pages/PageBuilder';
import MediaGallery from './pages/MediaGallery';
import Editor from './pages/Editor';

function App() {
  return (
    <ThemeProvider>
      <ShortcutsProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pages/builder" element={<PageBuilder />} />
            <Route path="/media" element={<MediaGallery />} />
            <Route path="/editor" element={<Editor />} />
          </Routes>
        </Layout>
      </ShortcutsProvider>
    </ThemeProvider>
  );
}

export default App;
