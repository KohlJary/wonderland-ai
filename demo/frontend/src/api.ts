/**
 * Backend API wrapper. Centralizes the HTTP details so feature
 * components don't repeat fetch+JSON+error handling. Vite's dev
 * server proxies /api → http://localhost:8000 (see vite.config.ts).
 *
 * Contracts:
 * - contract-note-01KRXRTT: Note model and CRUD endpoint contract
 * - contract-note-002: Search endpoint shape
 *
 * POST /api/notes: {title, body, tag_names} → {id, title, body, tag_names, tag_ids, created_at, updated_at}
 * GET /api/notes: → [{id, title, body, tag_names, tag_ids, created_at, updated_at}] (reverse chronological)
 * GET /api/notes/{id}: → {id, title, body, tag_names, tag_ids, created_at, updated_at}
 * PUT /api/notes/{id}: {title?, body?, tag_names?} → {id, title, body, tag_names, tag_ids, created_at, updated_at}
 * DELETE /api/notes/{id}: → 204 no content
 * GET /api/search: ?q=...&tags=...&page=...&page_size=... → {results: [...], total_results, page, page_size, has_more}
 */

export interface Note {
  id: number;
  title: string;
  body: string;
  tag_names: string[];
  tag_ids: number[];
  created_at: string;
  updated_at: string;
  revision_id: string;  // Opaque string for collision detection (If-Match header)
}

export interface NoteCreateRequest {
  title: string;
  body?: string;
  tag_names?: string[];
}

export interface NoteUpdateRequest {
  title?: string;
  body?: string;
  tag_names?: string[];
}

export interface SearchResultNote {
  id: number;
  title: string;
  body_preview: string;  // First 150 chars of body
  tag_names: string[];
  tag_ids: number[];
  created_at: string;
  updated_at: string;
  revision_id: string;  // Opaque string for collision detection (If-Match header)
}

export interface SearchResponse {
  results: SearchResultNote[];
  total_results: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

/**
 * ConflictError — the response body from a 409 Conflict when PUT /api/notes/{id} 
 * detects an If-Match header mismatch.
 *
 * Contract reference: contract-note-01KRY0B8 (collision-detection-contract)
 * Backend returns this structure when client's If-Match doesn't match server's current revision_id.
 */
export interface ConflictError {
  error: 'ConflictError';
  message: string;  // Descriptive message from backend
  server_revision_id: string;  // Current revision_id on the server
  server_state: Note;  // Backend's current note state (includes new revision_id)
}

export async function createNote(payload: NoteCreateRequest): Promise<Note> {
  const res = await fetch('/api/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: payload.title,
      body: payload.body || '',
      tag_names: payload.tag_names || [],
    }),
  });
  if (!res.ok) {
    const error = await res.text();
    throw new Error(`createNote failed: ${res.status} ${res.statusText} — ${error}`);
  }
  return res.json();  // Response includes revision_id per contract-note-01KRY0B8
}

export async function listNotes(): Promise<Note[]> {
  const res = await fetch('/api/notes');
  if (!res.ok) {
    throw new Error(`listNotes failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function readNote(id: number): Promise<Note> {
  const res = await fetch(`/api/notes/${id}`);
  if (!res.ok) {
    throw new Error(`readNote failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function updateNote(
  id: number,
  payload: NoteUpdateRequest,
  revisionId?: string  // If-Match header value for collision detection
): Promise<Note | { conflict: ConflictError }> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (revisionId) {
    headers['If-Match'] = revisionId;
  }

  const res = await fetch(`/api/notes/${id}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(payload),
  });

  // Handle 409 Conflict: return conflict data so caller can show modal
  if (res.status === 409) {
    const responseBody = await res.json();
    
    // FastAPI wraps the HTTPException detail in a 'detail' field.
    // The detail contains our conflict response: {error, message, server_revision_id, server_state}
    // Per contract-note-01KRY0B8, the 'message' field is ALWAYS present and is NOT optional.
    const conflictData = responseBody.detail || responseBody;
    
    // Type-check the conflict response to ensure it has the expected shape
    if (
      conflictData &&
      typeof conflictData === 'object' &&
      'error' in conflictData &&
      'message' in conflictData &&
      'server_revision_id' in conflictData &&
      'server_state' in conflictData
    ) {
      const typed: ConflictError = {
        error: conflictData.error as 'ConflictError',
        message: conflictData.message,  // Contract guarantees this is present; no fallback needed
        server_revision_id: conflictData.server_revision_id,
        server_state: conflictData.server_state,
      };
      return { conflict: typed };
    }
    
    // If response shape doesn't match expected, throw error
    // (message missing indicates a backend bug in adhering to contract-note-01KRY0B8)
    throw new Error(`updateNote 409 Conflict response has unexpected shape: ${JSON.stringify(conflictData)}`);
  }

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`updateNote failed: ${res.status} ${res.statusText} — ${error}`);
  }
  return res.json();
}

export async function deleteNote(id: number): Promise<void> {
  const res = await fetch(`/api/notes/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error(`deleteNote failed: ${res.status} ${res.statusText}`);
  }
}

export async function searchNotes(
  q?: string,
  tags?: string,
  page: number = 1,
  page_size: number = 20
): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (q) params.append('q', q);
  if (tags) params.append('tags', tags);
  params.append('page', String(page));
  params.append('page_size', String(page_size));
  
  const res = await fetch(`/api/search?${params.toString()}`);
  if (!res.ok) {
    throw new Error(`searchNotes failed: ${res.status} ${res.statusText}`);
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
