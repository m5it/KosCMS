import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ShortcutsProvider } from './context/ShortcutsContext';
import AdminShell from './admin/AdminShell';

function App() {
  return (
    <ThemeProvider>
      <ShortcutsProvider>
        <Routes>
          <Route path="/admin/*" element={<AdminShell />} />
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </ShortcutsProvider>
    </ThemeProvider>
  );
}

export default App;
