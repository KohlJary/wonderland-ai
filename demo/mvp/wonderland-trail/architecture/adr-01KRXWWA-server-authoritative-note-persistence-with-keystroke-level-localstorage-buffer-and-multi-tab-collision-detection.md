# ADR-004: Server-authoritative note persistence with keystroke-level localStorage buffer and explicit Save in hybrid-offline mode

**GUID:** 01KRXWWAB5BG6H6VH19PDBMC96

## Context

Kohl needs offline-capable note creation. The operator has specified: "App must function offline; localStorage is the optional persistence layer, not required for core functionality." Within this offline-capable scope, three models are coherent: (1) offline-first with automatic sync (Kohl edits offline, changes sync when backend is available), (2) online-first with keystroke recovery (Kohl must be connected to Save, localStorage only protects against page reload within a session), (3) hybrid (Kohl can edit offline, but Save is explicit and user-initiated). The operator chose hybrid-offline semantics.

Under hybrid-offline: Kohl's keystrokes survive network loss during an editing session (localStorage buffers them); her deliberate Save action is when she chooses to sync (requires backend availability in v1; v1.5 will add offline queuing). This decision cascades into the save endpoint contract, sync semantics, and audit-trail logging.

The server must remain the source of truth for 'saved' state. Users may accidentally open multiple editor tabs; silent overwrites are unacceptable. The audit trail must log every saved state for compliance and forensic reconstruction. The directive specifies web runtime with SQLite persistence.

## Decision

Implement server-authoritative persistence with these semantic layers:

1. **Keystroke buffer in localStorage** — on every keystroke in title or body, write to localStorage under a stable key ('editor_draft'); survives page reload and network loss during an active editing session. Cleared after successful Save. User-invisible; no UI signals that content is 'buffered' vs. 'saved.'

2. **Explicit Save button** — user-facing commitment to persist. Calls POST /notes with {title, body, tag_names} and receives {id, revision_id, created_at, updated_at}. Revision_id is cryptographically opaque (deterministic hash of saved state), returned to client for collision detection on future Save attempts.

3. **Collision detection** — client tabs track revision_id from the last successful Save. Before attempting a new Save, client compares buffered state against current revision on backend (via GET /notes/:id endpoint or stored revision_id from prior Save). If stale, display collision warning: "Another tab has saved changes since you last synced. Your unsaved changes are [title], [body preview]. Would you like to: (a) Reload and see the server's version, (b) Overwrite with your version, (c) Cancel?" User chooses; Save proceeds only with explicit choice.

4. **Audit trail** — every successful Save creates an immutable log entry. Schema: {note_id FK, timestamp, user_id, saved_state_json (full snapshot), revision_id (opaque hash), state_hash (tamper detection)}. Full-state snapshots (not deltas) for forensic clarity and query simplicity.

5. **Single-user assumption** — no multi-device sync, no CRDT, no merge logic. Offline is per-session on one device. Once Kohl saves, the backend is the authoritative version; no eventual-consistency scenarios within v1.

## Tradeoffs

- **Explicit Save vs. automatic sync:** Explicit Save (user-initiated) keeps the backend contract simple—no background-sync logic, no queue management, no partial-write recovery. The cost is UX explicitness (user must consciously save, not implicit background persistence). For Kohl's research workflow (discrete editing sessions, deliberate note creation), explicit Save aligns with her mental model and adds no cognitive overhead. Fast-follow (v1.5): background sync for offline queuing if Kohl tries to Save without network.

- **v1 requires backend availability for Save:** Keystroke buffer protects against page reload, not network loss at the Save moment. If Kohl tries to Save while offline in v1, the Save fails and the buffer is preserved (user can retry when network returns). This is acceptable for single-researcher, single-device scope. v1.5 will queue the Save and retry on reconnection.

- **Device-loss risk inherent to offline-first:** Plaintext content in localStorage is protected by OS device lock (assumed: MacOS/Windows/Linux with user login required). No encryption-at-rest in v1. If Kohl's device is stolen and the OS is compromised, notes are readable. This is an accepted risk for a local-development tool; future work (v2) can add encryption if threat model evolves.

- **Revision identifiers are cryptographically opaque:** Hash-based (not sequential counters) to prevent prediction and malleability attacks. Deterministic so that identical saves produce identical revision IDs (idempotency property). The specific algorithm (SHA256, BLAKE3, etc.) is deferred to M3 contract negotiation; the architectural commitment is determinism and unforgeability. Opaque identifiers prevent an attacker (or buggy code) from crafting a collision by predicting future revision IDs.

- **Audit trail uses full-state snapshots, not deltas:** Trades storage cost for query simplicity and forensic clarity. Storage growth is linear with save frequency (N saves × size-of-one-note). For Kohl's v1 scale (estimated <1000 notes, <10k total saves), SQLite handles this comfortably; no sharding needed. Deltas would require replay logic to reconstruct prior state, which introduces a bug class (replay failures, timestamp ordering ambiguities, state divergence). Full snapshots eliminate this risk. If storage grows to be a constraint in v2+, switch to hybrid (snapshots every N saves + deltas in between) without changing the application contract.

- **Multi-tab collision detection (mandatory per ruling):** Client-side detection adds revision tracking and collision-warning UI. The benefit is prevention of silent data loss when Kohl accidentally opens two editor tabs. The cost is modest (cache revision_id from last Save, compare on Save attempt, display warning if stale). Server-side conflict resolution (CRDT, operational transform) was rejected because single-user assumption makes it unnecessary; client-side choice (user sees collision and decides) is simpler and aligns with Kohl owning all versions.

## Status

Proposed

## Notes for M3 Contract Negotiation (Tweedles)

- The save endpoint must return revision_id (opaque hash). The client caches this and uses it for collision detection on subsequent Save attempts.
- The hash algorithm choice (SHA256 vs. BLAKE3 vs. other) and the exact serialization of 'saved state' for hashing (title + body + tags? include timestamps?) should be specified in the save-endpoint contract note.
- The GET /notes/:id endpoint should include revision_id in the response so the client can validate staleness on collision detection.
- Collision warning UI is the user-facing surface; implementation detail is client-side comparison of cached revision_id against server's current revision_id. If different, state is stale and warning should be shown.
