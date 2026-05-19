# ADR-001: Client-buffered, server-authoritative note persistence

**GUID:** 01KRXRS3HMB08KMQM77QAH6A8V

## Context

The stories define two client-side concerns (localStorage keystroke buffer, markdown preview) and server-side persistence (CRUD endpoints for notes + tags). They do not specify the boundary contract: whether the client or server is the source of truth for note data. The Queen's question exposes this gap. The Tweedles cannot implement against an implicit contract.

## Decision

Adopt client-buffering, server-authoritative semantics: the client maintains a localStorage keystroke buffer as a write-ahead log and recovery mechanism. When the user saves (explicit or timeout-driven), the buffer is flushed to the server as a complete note state (title + body + tag IDs). The server persists this as canonical and returns the persisted note (with server-assigned timestamps and IDs). Tags are server-owned; the client displays them but does not persist them locally. On page reload, the client clears the buffer and fetches fresh note state from the server.

## Tradeoffs

- Rejects client-authoritative semantics: avoids the need to implement operational transform or CRDT-style conflict resolution, which is complex and unnecessary for a single-user note app. Cost: if Kohl ever shares note editing with others, we'd have to add conflict resolution retroactively.
- Rejects ephemeral client-only tags: tags are server-owned, not client-cached. Cost: tag operations require a server round-trip (can't be instant); benefit is that tag state is never stale and multiple clients see the same tags.
- Commits to a fetch-on-load pattern: page reload clears local state and fetches fresh. Cost: temporary loss of draft if user forgets to save; benefit is clarity (server is always the source of truth, no merge-on-load complexity).
- Requires explicit save semantics: the client does not auto-sync in the background. Cost: user must remember to save; benefit is that the user has explicit control over when their edits become persistent (no surprise server-side updates).

## Status

Proposed
