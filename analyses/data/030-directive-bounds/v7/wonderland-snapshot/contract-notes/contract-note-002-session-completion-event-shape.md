## Contract Note 002: Session completion event shape

**State:** clarification_needed
**Contract Version:** (locked, pending clarification)

**Current Shape:**

Frontend POSTs to POST /sessions with body: { focus_duration_seconds (int), break_duration_seconds (int), session_type ('focus'|'break'), started_at (ISO8601), completed_at (ISO8601) }. Backend stores this as an immutable fact keyed to (user_id, session_id, completed_at). Response is { session_id (UUID), recorded_at (ISO8601), ok: true }.

**Proposed Question for Clarification:**

Session ID generation: the proposed shape says backend stores keyed to `(user_id, session_id, completed_at)`, but the completion event from frontend does not include session_id. Questions:

1. Does frontend generate session_id locally (UUID v4) before starting a session, and include it in the completion POST?
2. Does backend generate session_id on receipt of completion POST, and return it in the response?
3. Or is session_id derived from some other field (e.g., hash of user_id + started_at + completed_at)?

Looking at the test scenarios (test_feature_001_edge_cases.py::test_feature_001_edge_duplicate_session_completion_idempotent), the test POSTs with `session_id` in the payload, expecting idempotent deduplication on `(session_id, completed_at)` pair. This implies frontend generates session_id locally.

**Frontend Impact (Tweedledee):**

If frontend generates session_id: I'll generate a UUID v4 when the session starts (POST /sessions/start or internally), store it in the session state envelope, and include it when POSTing completion. Idempotency follows naturally — retry with the same session_id + completed_at is a duplicate and backend recognizes it.

If backend generates session_id: I'll need backend to return session_id in the POST /sessions/start response, then I'll include it in the completion POST. Idempotency still works.

The test suite assumes frontend generates session_id (tests pass explicit session_id in completion POST). Recommend: **frontend generates, includes in completion POST**.

**Backend Impact (Tweedledum):**

Backend receives session_id from frontend completion POST. Backend enforces uniqueness of (user_id, session_id, completed_at) to ensure idempotent retries (second POST with same key returns the existing record, 200 OK, does not create duplicate).

**Resolution Path:**

Confirm frontend generates session_id locally. If backend needs to generate it instead, contract will change and test scenarios will need adjustment.

**Notes:**

Test scenario expects `session_id` in the POST /sessions/complete payload. If this is wrong, the test should be fixed. Otherwise, assume frontend generates UUID v4 for session_id on session start, includes in completion POST, and backend uses it for idempotency keying.
