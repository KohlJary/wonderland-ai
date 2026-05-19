# ADR-002: Server-authoritative note persistence with client-side keystroke buffer

**GUID:** 01KRXRT0GW02FT1Y7FZP513ZHG

## Context

The stories describe two persistence layers: client-side localStorage keystroke buffer (for resilience across page reloads) and server-side CRUD endpoints + SQLite (for durable storage). The Queen's security question exposes the need to specify the boundary contract: what data crosses the client/server boundary, in what form, and with what guarantees? The existing proposal names the architectural poles (server-authoritative vs. client-authoritative) but does not specify the security implications of the chosen architecture.

## Decision

Adopt server-authoritative note persistence: the client maintains a localStorage keystroke buffer as a write-ahead log for recovery and recovery only. When the user saves (explicit button click), the full note state (title + body + tag IDs) is posted to POST /notes or PATCH /notes/{id}. The server persists this as canonical state and returns the persisted note with server-assigned id, timestamps, and tag associations. On page reload, the client clears its localStorage buffer and fetches the persisted note from GET /api/notes/{id} (or GET /api/notes if creating a new note). Tags are server-owned throughout; the client displays tag state but does not cache or buffer it. The save button is the only sync point; there is no background or timeout-driven sync.

## Tradeoffs

- Rejects client-authoritative (optimistic update + merge-on-load): avoids CRDT/OT complexity unsuitable for a single-user note app. Cost: if Kohl shares editing with others in future, we rebuild the sync layer. Acceptable for v1 single-user scope.
- Rejects background/timeout-driven sync: the save button is the only sync trigger. Cost: if Kohl types but forgets to save and closes the tab, unsaved edits are lost (localStorage is cleared on load). Benefit: explicit user control over when edits become persistent; no surprise server-side mutations. Acceptable given the story's emphasis on keystroke survival (page reload without loss), not offline editing.
- localStorage holds plaintext note content: title and body in clear text, unencrypted. Cost: if device is compromised (malware, physical theft), note content is readable. Benefit: no client-side crypto complexity; localStorage is already device-locked (OS device lock is the security boundary). Acceptable for a local research notebook on a personal developer machine.
- Sync path is HTTPS only (enforced by web runtime): all POST/PATCH/GET requests to /api/notes/* must be over TLS. Cost: assumes standard HTTPS deployment; no custom transport security needed. Benefit: plaintext content is protected in flight.
- No conflict resolution, no audit trail of keystrokes: the audit trail captures only explicit saves (complete note states), not keystroke deltas. Single-user assumption means no simultaneous-tab conflicts to resolve. Cost: no keystroke-level undo/redo, no multi-tab awareness. Benefit: audit trail is simple (note versions only) and conflict resolution is unnecessary. Acceptable for single-user scope; if shared editing is added later, both audit and resolution layers must be redesigned.
- Tags are server-owned (no client caching): tag operations (add, remove) require server round-trips. Cost: tag UI is not instant (POST /notes/{id} with updated tag_ids, wait for response, update UI). Benefit: tag state is canonical and shared across any future clients (if Kohl opens the app in multiple browsers, tags are always in sync). Necessary for future multi-device support; acceptable single-user latency tradeoff for v1.

## Status

Proposed
