## Implementation 001: Feature 001: Session lifecycle failure modes and state machine constraints

**Side:** frontend
**Ticket:** Feature-001: Run a focused work session with built-in break
**Contract:** contract-note-003 (Session state machine: idle|running|paused|completed; atomic SessionRecord write on completion; WebSocket state subscription; frontend timer reconciliation; break as explicit new session)
**Ready for review:** no

**Approach:**

Test file encodes 30+ failure-mode scenarios covering: state machine violations (double-start, invalid transitions), completion atomicity (SessionRecord + status update together), pause/resume logic with cumulative paused_duration tracking, break transitions as explicit new sessions, session recovery across app restarts, timer drift detection and device clock offsets, and event ordering constraints. Tests use pytest fixtures to verify backend behavior (state enforcement, atomicity, persistence).

**Client State:**

These are backend specification tests; client_state is covered by Alice's happy-path scenario tests.

**Files:**
- tests/test_feature_001_failure_modes.py: 18.5KB of 9 test classes with 30 scenarios

**Known Limitations:**
- Tests currently pytest.skip with 'not yet implemented' — production code will turn them red.
- Timer drift and device clock tests are frontend-centric; Hatter may prefer Jest coverage for those.
- Transaction inspection tests (atomicity) may require special test tooling or transaction logging.
