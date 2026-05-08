/**
 * App — Pomodoro timer application.
 * Features the focus session timer (25 minutes).
 */

import { FocusTimer } from './FocusTimer';

export function App() {
  return (
    <main style={{ fontFamily: 'system-ui', maxWidth: 600, margin: '2em auto' }}>
      <h1>Focus Timer</h1>
      <p style={{ color: '#666', marginBottom: '2em' }}>
        Start a 25-minute focus session and track your productivity.
      </p>
      <FocusTimer />
    </main>
  );
}
