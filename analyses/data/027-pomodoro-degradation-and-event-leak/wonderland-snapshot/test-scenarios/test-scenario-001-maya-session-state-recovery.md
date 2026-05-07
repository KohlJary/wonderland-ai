## Test Scenario 001: Maya Session State Recovery

**Source Story:** story-006-maya-loads-her-session-after-a-day-away

**Narrative:**
Maya opens the app after 18 hours away. She expects her prior context (which books she was moderating, which language pairs were active) to be exactly as she left it. The session loads within 2 seconds.

**Acceptance Criteria:**
- Session ID is identical before and after app closure
- All session fields are restored exactly (startTime, targetDuration, personaTag, etc.)
- No data is lost or reset between app restarts
- Load completes within 2 seconds

**Severity:** CRITICAL

**Test File:** `tests/test_session_persistence_maya_state_recovery.py`

**Test Cases:**
1. `test_maya_session_state_persists_across_app_closure` — Core persistence across long absence
2. `test_maya_language_pairs_persisted_with_session` — Language pair context restored
3. `test_multiple_sessions_restore_independently` — Multiple sessions restore distinctly
4. `test_maya_session_state_exact_match_before_and_after_closure` — Bit-identical restore
5. `test_no_session_data_lost_on_app_reopen` — All fields present on restore

**Backend Implementation Requirement:**
- GET /sessions/{id} must return complete session record with all fields
- Session record must be persisted to disk (not memory-only)
- Load must support long gaps (hours/days) between request and next request

**Concern:**
Sessions are stored in IndexedDB (M1 client-only). The test assumes a TestClient with in-memory DB mocking production-like persistence. Contract still needs clarification on whether sessions are *also* stored server-side or client-only.
