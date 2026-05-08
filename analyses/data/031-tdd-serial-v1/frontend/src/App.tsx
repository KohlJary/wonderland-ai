/**
 * App — main UI orchestrator.
 * Routes between timer views and settings screen.
 */

import { useEffect, useState } from 'react';
import { SettingsScreen } from './SettingsScreen';
import { getSettingsManager } from './settings';

export function App() {
  const [currentView, setCurrentView] = useState<'timer' | 'settings'>('timer');
  const manager = getSettingsManager();
  const settings = manager.current();

  // Apply theme to document root
  useEffect(() => {
    const unsubscribe = manager.onChange((newSettings) => {
      if (newSettings.theme === 'dark') {
        document.documentElement.style.colorScheme = 'dark';
        document.documentElement.style.backgroundColor = '#1a1a1a';
        document.documentElement.style.color = '#e0e0e0';
      } else {
        document.documentElement.style.colorScheme = 'light';
        document.documentElement.style.backgroundColor = '#fff';
        document.documentElement.style.color = '#000';
      }
    });

    // Apply initial theme
    if (settings.theme === 'dark') {
      document.documentElement.style.colorScheme = 'dark';
      document.documentElement.style.backgroundColor = '#1a1a1a';
      document.documentElement.style.color = '#e0e0e0';
    }

    return unsubscribe;
  }, [manager, settings]);

  return (
    <div style={{
      minHeight: '100vh',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      transition: 'background-color 0.3s, color 0.3s',
    }}>
      {currentView === 'timer' ? (
        <TimerView onNavigateSettings={() => setCurrentView('settings')} />
      ) : (
        <SettingsScreenWithNav onBack={() => setCurrentView('timer')} />
      )}
    </div>
  );
}

function TimerView({ onNavigateSettings }: { onNavigateSettings: () => void }) {
  return (
    <main style={{ maxWidth: 600, margin: '2em auto', padding: '0 1em' }}>
      <h1>fullstack-app</h1>
      <p style={{ color: '#999', fontStyle: 'italic' }}>
        Feature components to be added (focus session timer, break timer, daily review).
      </p>
      <button
        onClick={onNavigateSettings}
        style={{
          padding: '0.75em 1.5em',
          fontSize: '1em',
          backgroundColor: '#0066cc',
          color: 'white',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
        }}
      >
        ⚙️ Settings
      </button>
    </main>
  );
}

function SettingsScreenWithNav({ onBack }: { onBack: () => void }) {
  return (
    <div>
      <div style={{
        padding: '1em',
        borderBottom: '1px solid #ccc',
        display: 'flex',
        alignItems: 'center',
        gap: '1em',
      }}>
        <button
          onClick={onBack}
          style={{
            padding: '0.5em 1em',
            backgroundColor: '#999',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          ← Back
        </button>
      </div>
      <SettingsScreen />
    </div>
  );
}
