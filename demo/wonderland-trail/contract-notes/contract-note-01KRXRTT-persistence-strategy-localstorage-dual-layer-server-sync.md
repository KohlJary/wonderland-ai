## Contract Note 002: Persistence strategy: localStorage dual-layer + server sync

**GUID:** 01KRXRTTX8132D8F41PJS7GRK3
**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None — not yet specified

**Proposed Change:**

Backend serves as persistence layer; frontend uses localStorage as keystroke buffer (data-local writes) and fetches from server on reload. Keystroke debounce (500ms) before syncing to server. On page load, fetch current state from server and hydrate frontend. No conflict resolution v1 — last write wins. DELETE endpoints hard-delete; no soft-delete/trash v1.

**Source:** Requirement: keystroke-level persistence with dual-layer strategy; offline-capable app; five-minute setup bar.

**Frontend Impact (Tweedledee):**

Accepted with two clarifications needed from Tweedledum: (1) When I POST to /api/notes with title + body, does the server assign an id and return it in the response? (The new note needs an id so future saves use PATCH /api/notes/{id}, not POST again.) (2) On page reload, if I have a note_id in state, I fetch GET /api/notes/{id}; if no id (fresh page), I initialize empty editor and wait for first save. Is this the intended flow, or should I check localStorage for unsaved edits and restore them pre-fetch? (The ADR says localStorage clears on load, which implies I start fresh, but want to confirm.) 500ms debounce is implementable; I'll use setTimeout with cancel-on-unmount. Keystroke buffer in localStorage is local state (useEffect + useState); no cross-component sharing needed.

**Backend Impact (Tweedledum):**

Endpoints must handle frequent updates (debounced from client, but still ~5-10/min per note during active editing). No conflict handling — assume client state is canonical on PUT. Return full note on all mutating responses so client can update local state atomically. Error responses must distinguish retryable (5xx, network) from client errors (4xx).
