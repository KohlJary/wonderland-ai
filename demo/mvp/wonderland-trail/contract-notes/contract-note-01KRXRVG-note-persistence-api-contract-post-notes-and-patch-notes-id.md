## Contract Note 003: Note persistence API contract: POST /notes and PATCH /notes/:id

**GUID:** 01KRXRVG5Q663M7EWHMCN7K0NW
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

ADR-002 specifies: client posts complete note state (title + body + tag IDs) to POST /notes or PATCH /notes/:id. Server persists and returns persisted note. localStorage buffer is write-ahead log only.

**Proposed Change:**

Formalize the request/response shapes, error handling, and reconciliation semantics for the client-buffered-server-authoritative contract.

**Source:** ticket-01KRXRNH-frontend-editor-pane-with-title-input-markdown-body-editor-and-keystroke-buffer-to-localstorage (acceptance criteria require clarity on save button flow)

**Frontend Impact (Tweedledee):**

Request shape: Editor buffers {title, body, tag_ids} to localStorage on each keystroke; Save button POSTs {title, body, tag_ids: string[]} to POST /notes (create) or PUT /notes/{id} (update existing). Response must be {id, title, body, created_at, updated_at, tags: Tag[]} with server-assigned timestamps and id. On success: clear localStorage, update editor state with server-returned id (so future saves use PUT not POST). On error (400, 409 conflict, etc.): display error text to user (show in UI state: error-recoverable), preserve localStorage buffer, keep Save button clickable for retry. On page reload: if localStorage exists, show Restore button + clear button; if no localStorage, start fresh or fetch existing note if URL has /notes/{id}.

**Backend Impact (Tweedledum):**

Confirming settled contract: Request body for POST /notes and PUT /notes/{id} is {title: string (1-255 chars, required), body: string | null (optional, max 16384 chars), tag_names: string[] (optional)}. Response is {id, title, body, tag_names: string[], tag_ids: int[], created_at: ISO8601 UTC, updated_at: ISO8601 UTC}. Body field is stored raw (no HTML sanitization or markdown processing on backend). Client is responsible for sanitizing parsed markdown on render. Tags in request are names (tag_names: string[]); response includes both names and IDs (tag_names and tag_ids).
