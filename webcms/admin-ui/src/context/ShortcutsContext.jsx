import React, { createContext, useContext } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';

const ShortcutsContext = createContext(null);

export function ShortcutsProvider({ children }) {
  useHotkeys('ctrl+s, meta+s', (event) => {
    event.preventDefault();
    window.dispatchEvent(new CustomEvent('cms:save'));
  });

  useHotkeys('ctrl+n, meta+n', () => {
    window.dispatchEvent(new CustomEvent('cms:new'));
  });

  useHotkeys('ctrl+d, meta+d', () => {
    window.dispatchEvent(new CustomEvent('cms:darkmode'));
  });

  useHotkeys('esc', () => {
    window.dispatchEvent(new CustomEvent('cms:close'));
  });

  return (
    <ShortcutsContext.Provider value={{}}>
      {children}
    </ShortcutsContext.Provider>
  );
}

export function useShortcuts() {
  return useContext(ShortcutsContext);
}
