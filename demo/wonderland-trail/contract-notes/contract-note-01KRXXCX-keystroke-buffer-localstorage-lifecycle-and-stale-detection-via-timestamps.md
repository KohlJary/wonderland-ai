## Contract Note 013: Keystroke buffer: localStorage lifecycle and stale-detection via timestamps

**GUID:** 01KRXXCXQ0SXWWEFDGDFHJKKTM
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Contract-note-003 says 'clear localStorage after successful save' but doesn't specify how client detects whether localStorage is stale on page reload.

**Proposed Change:**

Client buffers keystrokes to localStorage as {title, body, tag_names, lastSyncedAt: ISO8601 (copied from server.updated_at at time of last successful save)}. On successful POST or PUT: client updates lastSyncedAt = server.updated_at from the response. On page reload: (a) if localStorage exists, fetch the note's current state (GET /notes/{id}); (b) if localStorage.lastSyncedAt < server.updated_at, show Restore button + Discard button (user has unsaved changes); (c) if timestamps match, localStorage is in sync (silently discard it); (d) if no localStorage, start fresh or load existing note via GET. For v1, assume single-user single-tab (no merge UI needed). On successful save, buffer/updated_at should also be cleared when save completes.

**Source:** Tweedledee Q2 (keystroke buffer and sync semantics).

**Frontend Impact (Tweedledee):**

I buffer keystrokes to localStorage as {id, title, body, tag_names, lastSyncedAt}. On successful POST/PATCH, I update lastSyncedAt = server.updated_at from response. On page reload: (a) if localStorage exists, fetch GET /notes/{id}; (b) if localStorage.lastSyncedAt < server.updated_at, show Restore Draft vs. Load Latest UI (user chooses); (c) if timestamps match, silently discard localStorage and load server state; (d) if no localStorage, load server state. For v1, assume single-user single-tab, so no merge logic needed — just a choice for the user. On successful save, clear the localStorage buffer.

**Backend Impact (Tweedledum):**

None. Continue returning updated_at in every note response. No schema changes.
