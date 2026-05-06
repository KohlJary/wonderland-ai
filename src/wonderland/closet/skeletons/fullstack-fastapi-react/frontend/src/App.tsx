/**
 * App — placeholder UI demonstrating end-to-end fetch + render.
 * Lists messages and lets you post a new one. Replace with the
 * actual feature UI; this exists so the seed has a working
 * backend↔frontend flow for the human verifying it.
 */

import { useEffect, useState } from 'react';
import { listMessages, postMessage, type Message } from './api';

export function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMessages()
      .then(setMessages)
      .catch((e) => setError(String(e)));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!draft.trim()) return;
    try {
      const msg = await postMessage(draft);
      setMessages((prev) => [...prev, msg]);
      setDraft('');
      setError(null);
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <main style={{ fontFamily: 'system-ui', maxWidth: 600, margin: '2em auto' }}>
      <h1>fullstack-app</h1>
      <p style={{ color: '#666', fontStyle: 'italic' }}>
        Placeholder UI — replace with real feature components.
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Type a message…"
          style={{ flex: 1, padding: 8 }}
        />
        <button type="submit">Send</button>
      </form>

      {error && (
        <p style={{ color: 'crimson' }}>{error}</p>
      )}

      <ul>
        {messages.map((m) => (
          <li key={m.id}>{m.text}</li>
        ))}
      </ul>
    </main>
  );
}
