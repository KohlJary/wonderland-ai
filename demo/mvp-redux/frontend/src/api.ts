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

export interface Note {
  id: number;
  title: string;
  body: string;
  tags: string[];
  created_at: string;
  updated_at: string;
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

// Notes API endpoints
export async function listNotes(): Promise<Note[]> {
  const res = await fetch('/api/notes');
  if (!res.ok) {
    throw new Error(`listNotes failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getNote(noteId: number): Promise<Note> {
  const res = await fetch(`/api/notes/${noteId}`);
  if (!res.ok) {
    throw new Error(`getNote failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function createNote(title: string, body: string, tags: string[]): Promise<Note> {
  const res = await fetch('/api/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body, tags }),
  });
  if (!res.ok) {
    throw new Error(`createNote failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function updateNote(
  noteId: number,
  title: string,
  body: string,
  tags: string[],
): Promise<Note> {
  const res = await fetch(`/api/notes/${noteId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, body, tags }),
  });
  if (!res.ok) {
    throw new Error(`updateNote failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function deleteNote(noteId: number): Promise<void> {
  const res = await fetch(`/api/notes/${noteId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`deleteNote failed: ${res.status} ${res.statusText}`);
  }
}

export async function searchNotes(query: string, signal?: AbortSignal): Promise<Note[]> {
  const params = new URLSearchParams({ q: query });
  const res = await fetch(`/api/notes?${params.toString()}`, { signal });
  if (!res.ok) {
    throw new Error(`searchNotes failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function filterNotesByTag(tag: string, signal?: AbortSignal): Promise<Note[]> {
  const params = new URLSearchParams({ tag });
  const res = await fetch(`/api/notes?${params.toString()}`, { signal });
  if (!res.ok) {
    throw new Error(`filterNotesByTag failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function searchAndFilterNotes(
  query?: string | null,
  tag?: string | null,
  signal?: AbortSignal
): Promise<Note[]> {
  /**
   * Composable search and filter.
   * Backend accepts both q and tag parameters simultaneously.
   * When both are provided, backend ranks results by relevance 
   * (exact tag match > title match > body match) with updated_at DESC tiebreaker.
   * If neither provided, returns all notes ordered by updated_at DESC.
   */
  const params = new URLSearchParams();
  if (query?.trim()) {
    params.append('q', query);
  }
  if (tag?.trim()) {
    params.append('tag', tag);
  }

  const url = params.toString() ? `/api/notes?${params.toString()}` : '/api/notes';
  const res = await fetch(url, { signal });
  if (!res.ok) {
    throw new Error(`searchAndFilterNotes failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
