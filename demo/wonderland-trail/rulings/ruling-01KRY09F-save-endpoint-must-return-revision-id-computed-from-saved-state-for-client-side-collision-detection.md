## Ruling 013: Save endpoint must return revision_id computed from saved state for client-side collision detection

**GUID:** 01KRY09F54DR6H71BJ2GH7NTQ0
**Severity:** critical
**Domain:** authorization
**Source:** operator_specification_and_hybrid_offline_architecture

**Citation:**

Architecture decision: server-authoritative persistence with hybrid-offline keystroke buffer (ADR-006). Collision detection requires clients to track revision_id and compare before overwriting (Queen Ruling 008). Operator specification: revision_id returned by server, computed after receiving user edits.

**Finding:**

The Save endpoint response shape determines whether multi-tab collision detection is possible at all. If the endpoint returns revision_id, clients can cache it and detect staleness on the next Save attempt (tab A saves first, returns revision_id-V1; tab B attempts save with cached revision_id-V0, detects mismatch, warns user). If revision_id is not returned, tabs cannot detect collisions — they would both believe they have the latest version and the second Save would silently overwrite the first. The operator's choice (server returns revision_id) makes collision detection implementable.

**Required Remediation:**

The Save endpoint (POST /api/notes and PUT /api/notes/:id) must include revision_id in the response JSON. The revision_id is computed server-side as a cryptographically opaque hash of the saved state (deterministic per Queen Ruling 009: same title+body+tags always produces same hash). The client receives the new revision_id, caches it in localStorage, and compares it on the next Save attempt to detect if another tab has written a newer version.

**Acceptance Criteria:**
- POST /api/notes response includes revision_id field with opaque hash value
- PUT /api/notes/:id response includes revision_id field with opaque hash value
- revision_id is computed deterministically from saved state (same input always produces same hash)
- revision_id is included in the audit-trail log for this save event
- frontend can parse revision_id from response and store it for collision detection on next save

**Residual Risk:**

If the client fails to cache revision_id after a successful Save, or if localStorage is cleared between saves, the client loses the cached version and the next Save will not detect collisions from other tabs. This is acceptable risk for v1 single-user scope; the stored-on-browser assumption is that Kohl is aware of her own tab state. Fast-follow could add session sync (tabs sync revision_id via BroadcastChannel or SharedWorker) to eliminate this gap.

**Compliance Implications:**

None. revision_id is part of the audit trail (Queen Ruling 007) and the security contract (Queen Ruling 008), but has no compliance framework implications for v1.

**Audit Reference:**

Audit-trail logs will record: {timestamp, user_id (null in v1), saved_state: {title, body, tag_names}, revision_id: hash, state_hash: hmac}. The revision_id in the log matches the revision_id returned to the client.
