# ADR-005: Audit trail schema: full-state snapshots with timestamped revisions

**GUID:** 01KRXX854985KJ5FQ38PGTH40S

## Context

The Queen has ruled that every note save must produce an immutable, append-only log entry that includes timestamp, user_id, complete saved state, and state hash — complete enough for forensic reconstruction. The schema representation (what 'complete saved state' means in the log) affects storage cost, query performance, and the complexity of reconstruction logic. Three candidates: (1) Full snapshots: each log entry includes the entire note {title, body, tags, revision_id} at that save moment — simplest, fastest to query, largest storage. (2) Delta encoding: log entries include only the changes (diffs) from the prior state — compact, requires replay logic to reconstruct, slower queries. (3) Hybrid: snapshots at regular intervals + deltas in between — balance storage and query speed, moderate complexity. The choice does not affect the security requirement (the log must be immutable, complete, forensic-reconstructible); it affects the engineering tradeoff.

## Decision

Implement audit trail using full-state snapshots. Each log entry captures the complete saved state {title, body, tags, revision_id, timestamp, user_id, state_hash} atomically. This choice optimizes for correctness and simplicity: (1) Every log entry is standalone and can answer 'what was this note at time T?' without reconstruction logic. (2) Storage growth is predictable (N saves × size-of-one-note), not dependent on edit frequency. (3) Queries are fast (single row lookup per timestamp). (4) The absence of reconstruction logic eliminates an entire class of bugs (replay failures, timestamp ordering ambiguities, state divergence between reconstructed and actual). For Kohl's single-device, single-user v1 scope, storage is not a constraint; correctness is paramount.

## Tradeoffs

- Storage cost grows linearly with save frequency (if Kohl saves 100 times, the audit log has 100 snapshots, not 100 deltas). For a single researcher with <1000 notes and <10k saves total (conservative estimate), SQLite will comfortably handle this; no sharding needed.
- Delta encoding was deferred because it adds reconstruction logic (replay) that could fail silently — Kohl might ask 'show me the note at 3pm' and get wrong state if replay has a bug. Full snapshots eliminate this risk in v1. If storage grows to be a problem in v2+, switch to hybrid (snapshots every N saves + deltas in between) without changing the application contract.
- The audit trail now has a concrete schema: audit_log table with (id PK, note_id FK, timestamp, user_id, saved_state JSON, revision_id, state_hash). The Tweedles will negotiate contracts against this. The revision_id field is the client-side handle for collision detection (opaque hash, returned to the client on save success); the audit_log records it so the team can trace any collision event back to the exact saved state.
- Forensic queries are now simple: 'SELECT * FROM audit_log WHERE note_id = X ORDER BY timestamp DESC LIMIT 1' gives the current state; 'SELECT * FROM audit_log WHERE note_id = X AND timestamp <= T ORDER BY timestamp DESC LIMIT 1' gives state at time T. No reconstruction logic needed.

## Status

Proposed
