# ADR-003: Server-authoritative note persistence with keystroke-level localStorage buffer

**GUID:** 01KRXRV72HAR9AKNZVPYFEYAP7

## Context

Kohl needs to capture experimental findings without losing work to browser restart (hence localStorage recovery) and to deliberately persist findings to a durable backend when ready (hence the explicit Save button). The stories name two persistence layers but do not specify their boundary contract. The Queen's questions expose this gap: is the client or server the source of truth? What data crosses the boundary, and in what form? The operator's constraint is explicit: 'localStorage on every keystroke, db only saves when button is pressed.' This defines the observable behavior; the architecture must serve it without introducing merge conflicts or sync ambiguity.

## Decision

Adopt server-authoritative note persistence with a client-side keystroke buffer. The client maintains a localStorage buffer that captures every keystroke of the note's title and body (for recovery on page reload). When Kohl clicks Save, the complete note state (title + body + tag IDs) is posted to the backend. The server persists this as canonical state (with server-assigned ID, timestamps, and tag associations), and returns the persisted note to the client. On page reload, the client clears its localStorage buffer and fetches fresh note state from the server. Tags are server-owned throughout; tag operations (add, remove) are only reflected after server confirmation. The Save button is the only sync point; there is no background sync, no optimistic updates, no conflict resolution.

## Tradeoffs

- Rejects client-authoritative (optimistic update semantics): avoids the need for CRDT or OT, which would be overengineering for a single-user note app with explicit Save semantics. Cost: if Kohl later shares editing with others, we'd retrofit conflict resolution. Acceptable for v1 single-user scope.
- Rejects background or timeout-driven sync: the Save button is the only trigger. Cost: if Kohl types and closes the tab without clicking Save, unsaved edits are lost (localStorage is cleared on reload). Benefit: explicit user control over when edits become persistent; Kohl's mental model is 'I save when I'm confident in my notes.' Acceptable given the keystroke-buffer requirement—localStorage survival addresses the unintended-reload case; intentional closure without save is not a failure.
- localStorage holds plaintext note content (title + body) unencrypted: Cost is device compromise exposure (malware, physical theft). Benefit is simplicity (no client-side crypto). The security boundary is the OS device lock, standard for single-user local apps. Queen's ruling covers XSS mitigation and buffer purge discipline.
- Sync path is HTTPS enforced: all API traffic is TLS-protected. Plaintext content in transit is protected by the transport layer.
- No keystroke-level audit trail: the server logs complete note states at save time, not keystroke deltas. Single-user scope means no simultaneous-tab conflicts to track. Cost: no keystroke-level undo/redo. Benefit: audit trail is simple (note versions only). Acceptable for v1; multi-user requires redesign.
- Tags are server-owned, no client-side caching: tag operations (add, remove, list) require server round-trips. Cost: tag UI is not instant—POST /notes/{id} with updated tag_ids, wait for 2xx response, update UI. Benefit: tag state is canonical and ready for future multi-device/multi-user support without rework.
- Explicit Save button, not auto-save: Cost is user must remember to save (though localStorage recovery reduces the impact of accidental closure). Benefit is user agency and predictability—Kohl knows exactly when notes become persistent. This aligns with the operator's constraint and Kohl's mental model of deliberate persistence.
- **Multi-tab collision detection is now mandatory** (per Queen's ruling): the single-user assumption does not prevent Kohl from opening the same note in two tabs by accident. Cost: client must track note revision state in localStorage and detect collisions before attempting to save (requires versioning the localStorage buffer and comparing against the server's last-saved version). The save endpoint must return a revision identifier so tabs can validate whether their buffered state is stale. Benefit: Kohl gets explicit warning if she tries to save conflicting edits from multiple tabs, with choice of which version to keep. This prevents silent data loss and aligns with Kohl's mental model of deliberate persistence ('I will not lose work without being asked'). The collision detection does not require CRDT or OT—the choice logic is simple (user picks tab A or tab B, the unchosen version is discarded but visible for manual merge if needed), and the audit trail records the choice for forensic clarity. This is a committed architectural requirement, not deferred.

## Status

Accepted

The Queen's ruling on multi-tab collision detection (Ruling 004) resolves the open question about accident-handling: yes, we detect and surface collisions to Kohl before overwrite. This does not change the fundamental server-authoritative architecture; it adds a client-side synchronization layer (localStorage versioning + collision detection) that makes the architecture resilient to accidental multi-tab edits. The Tweedles will negotiate the save endpoint contract (what version identifier format, how the client validates staleness) during M3 contract negotiation.
