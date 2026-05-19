# ADR-006: Server-authoritative note persistence with keystroke-level localStorage buffer and explicit Save in hybrid-offline mode

**GUID:** 01KRXXD4PRW69GQKV58EC55PBQ

## Context

Kohl needs offline-capable note creation. The operator has specified: 'App must function offline; localStorage is optional persistence layer.' Three offline models are coherent. The operator chose hybrid: Kohl edits offline (keystroke buffer in localStorage survives network loss), but Save is explicit (user decides when to sync to backend). This cascades into the save endpoint contract, sync semantics, and audit-trail logging. The prior ADR (server-authoritative persistence with keystroke buffering and collision detection) describes the correct architectural layers. This refined version grounds those layers in the operator's binding choice and the Queen's hash-semantics ruling.

## Decision

Implement server-authoritative persistence: (1) Keystroke buffer in localStorage on every keystroke; recovers on page reload; survives network loss during active editing session; cleared after Save. (2) Explicit Save button persists to backend via POST /notes, receives opaque revision_id (cryptographic hash of saved state) for collision detection. (3) Client collision detection compares cached revision_id against server's current version before Save; if stale, warning with user choice (reload, overwrite, or cancel). (4) Audit trail captures full-state snapshots at each Save: {note_id, timestamp, user_id, saved_state_json, revision_id, state_hash}. (5) Single-user, single-device, per-session offline scope; no multi-device sync or CRDT. (6) Backend is authoritative; localStorage is keystroke recovery buffer only.

## Tradeoffs

- Explicit Save keeps backend simple (no background sync, no queue management, no partial recovery). For Kohl's research workflow, explicit Save aligns with her mental model. v1.5 defers offline queuing.
- v1 requires backend availability for Save (keystroke buffer survives network loss, but Save action requires connection). Acceptable for single-device scope.
- Device-loss risk inherent to offline-first: plaintext in localStorage protected by OS device lock. No encryption-at-rest in v1.
- Revision identifiers are cryptographically opaque (hash-based, deterministic, unforgeable) to prevent malleability attacks and sequential-counter prediction. Specific algorithm (SHA256, BLAKE3, etc.) deferred to M3 contract negotiation.
- Audit trail uses full-state snapshots, not deltas: trades storage for query simplicity and forensic clarity. For Kohl's scale (<1000 notes, <10k saves), storage is not a constraint. Snapshots eliminate reconstruction-logic bugs.
- Multi-tab collision detection (mandatory per ruling) adds client-side revision tracking and collision-warning UI. Benefit: no silent data loss. Server-side CRDT was rejected (single-user scope makes it unnecessary).

## Status

Proposed
