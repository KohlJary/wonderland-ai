## Implementation 004: Feature 004: Settings customization failure modes and validation

**Side:** frontend
**Ticket:** Feature-004: Customize session and break lengths to fit personal rhythm
**Contract:** contract-note-005 (GET /api/settings returns {focus_session_length_minutes, break_length_minutes}; POST validates ranges [1-120] focus [1-60] break; session snapshots settings at creation; no backend WebSocket events v1; defaults created idempotently on first GET)
**Ready for review:** no

**Approach:**

Test file encodes 30+ failure-mode scenarios covering: input validation (ranges [1-120] focus, [1-60] break, no negatives/zero/fractional), idempotency (POST twice same values = idempotent), persistence (database durability, survival across restarts), non-retroactive application (settings snapshot at session creation, changes don't affect running session), response format consistency (both fields always present), error handling (failed POST doesn't corrupt existing settings, app survives settings load failure), and edge cases (break > session length allowed, rapid changes use latest).

**Client State:**

Frontend caches settings after fetch, optimistically updates on POST, shows 'Saving...' spinner, 'Saved' checkmark (auto-dismiss 1-2s), or error with retry. Tests verify backend provides fresh data and handles idempotent writes.

**Files:**
- tests/test_feature_004_failure_modes.py: 22.5KB of 10 test classes with 30 scenarios

**Open Questions for Pair:**
- Partial updates: contract doesn't specify if POST {focus: 40} (omitting break) should update only focus or error. Test scenarios document both possibilities.
- Fractional minutes: contract doesn't clarify if 25.5 should error or round. Test scenarios document both.
- Backend caching: contract says no cache, but test documents verification.

**Known Limitations:**
- Concurrency tests (rapid concurrent POSTs) are low-priority for single-user v1.
- Frontend caching logic (detect midnight, maintain cache TTL) is frontend's domain; consider Jest.
- DB failure injection tests may require special test tooling.
