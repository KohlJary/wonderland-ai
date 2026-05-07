## Implementation 001: Session persistence test scenarios and code (Alice stories 006, 007, 008)

**Side:** backend
**Ticket:** stories 006, 007, 008
**Contract:** contract-note-001 (session-persistence-api, state=counterpart_assessed). Session record: id (UUID), startTime (ISO8601), targetDuration (minutes), actualDuration (minutes|null), completionStatus (enum: pending|completed|extended), personaTag (string|null), breakTaken (boolean), createdAt (ISO8601). Operations: POST /sessions → 201 with full record; GET /sessions/{id} → 200; PATCH /sessions/{id} → 200; GET /sessions?fromDate=X&toDate=Y → 200. State machine: pending only → {completed, extended} (one-way). Concurrency: last-write-wins (M1 single-user).
**Ready for review:** yes

**Approach:**

Three pytest modules validate the persistence and recovery properties that the session API must satisfy. Maya module: state survives 18+ hour absence, all fields restored exactly, no data loss, multiple sessions restore independently. Kenji module: settings changes are non-blocking, no session reload, no ID change, completed sessions immutable. Jamie module: app close/reopen feels continuous, no stale-session timeout, no re-auth on reopen, ID stable across all operations, multi-device safe. Tests use TestClient fixture with in-memory SQLite; assume contract-note-001 shape and endpoints (POST /sessions, GET /sessions/{id}, PATCH /sessions/{id}, GET /sessions?fromDate=X&toDate=Y).

**Invariants Enforced:**
- Session ID never changes (tested across create, GET, PATCH, close/reopen, multiple devices)
- Session state is bit-identical after close/reopen (all fields match, no timestamps change)
- Completion state machine: pending → {completed|extended} only, no reversions
- Completed sessions immutable: PATCH rejected with 400
- Settings changes don't interrupt: no reload, ID unchanged, completionStatus unchanged
- Multi-session isolation: N sessions restore independently without data bleed
- No stale-session timeout: GET works hours/days after creation
- Session ID is the canonical lookup key and never changes during session lifetime

**Schema Changes:**

No schema changes in this commit. All tests validate against the schema in contract-note-001. M5 implementation will create the actual schema; tests will turn green when it does.

**Failure Modes Handled:**
- ID mismatch on reopen → test expects ID equality, fails if they differ
- Field loss or nullification → test expects all required fields, fails if missing
- Field value corruption → test expects bit-identical values, fails on delta
- Session reload on settings change → test expects createdAt unchanged, fails if it shifts
- Completed session mutation → test expects 400, fails if PATCH succeeds
- Data cross-contamination between sessions → test creates N and fetches independently, fails if A's data appears in B
- Stale-session deletion → test expects 200 even after idle hours, fails with 404
- State machine violation (backward transition) → test expects 400, fails if transition succeeds

**Files:**
- tests/test_session_persistence_maya_state_recovery.py: 5 tests on state persistence across closure
- tests/test_session_settings_change_midstream_kenji.py: 7 tests on non-blocking settings updates
- tests/test_session_close_reopen_jamie.py: 10 tests on app closure and recovery
- .wonderland/test-scenarios/test-scenario-001-maya-session-state-recovery.md
- .wonderland/test-scenarios/test-scenario-002-kenji-settings-midstream.md
- .wonderland/test-scenarios/test-scenario-003-jamie-close-reopen.md

**Open Questions for Pair:**
- Language pairs: are these nested in the session record (JSON field) or stored separately (foreign key to a pairs table)? Affects transaction boundaries and PATCH semantics. Tests include placeholders marking this TBD.
- Settings sync timing: when Kenji PATCHes to add a language pair, does the request block until server sync completes (today's assumption in tests), or queue locally and flush on timer/explicit sync? Buffered ops need different contract shape.
- Multi-device conflict resolution: Jamie story flags this. If device A completes a session and device B opens it later, do we merge, trust local cache, or trust server? Tests assume 'trust server' but contract should specify.
- Stale-session timeout: do sessions have a TTL (e.g., 30 days) after which they're auto-deleted? Tests assume no timeout (access works hours/days later); contract should clarify.
- Scroll position / viewport state: Jamie story confusion flags. Are these part of session persistence or deferred? Tests assume deferred; confirm scope.

**Known Limitations:**
- Tests are RED and will FAIL until M5 backend implementation. By design — red→green→refactor cycle validates contract.
- Language pairs shape is TBD. Tests include comments marking where the contract shape is needed; implementation should update test placeholders once shape is locked.
- Settings broadcast timing is TBD. Tests assume immediate blocking PATCH; buffered ops need contract amendments and separate test variations.
- Performance assertions deferred. Contract-note-001 names <50ms write and <200ms query targets; tests don't measure. Dormouse owns observability; profiling in follow-up.
- Timezone and clock resilience deferred to later. Separate test modules exist (test_session_clock_resilience.py); Hatter's future work.
