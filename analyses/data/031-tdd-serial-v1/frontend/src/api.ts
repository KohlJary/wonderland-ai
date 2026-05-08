/**
 * Backend API wrapper. Centralizes the HTTP details so feature
 * components don't repeat fetch+JSON+error handling. Vite's dev
 * server proxies /api → http://localhost:8000 (see vite.config.ts).
 */

export interface Message {
  id: number;
  text: string;
  created_at: string;
}

export async function listMessages(): Promise<Message[]> {
  const res = await fetch('/api/messages');
  if (!res.ok) {
    throw new Error(`listMessages failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function postMessage(text: string): Promise<Message> {
  const res = await fetch('/api/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(`postMessage failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch('/health');
  if (!res.ok) {
    throw new Error(`checkHealth failed: ${res.status}`);
  }
  return res.json();
}
