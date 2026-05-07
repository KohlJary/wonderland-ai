## Review 001: test_feature_001_state_machine.py and test_feature_002_today_count.py

**Files reviewed:** tests/test_feature_001_state_machine.py, tests/test_feature_002_today_count.py
**Verdict:** request-changes

### Findings

#### change-required: Inconsistent assumptions about Session response shape
**Location:** tests/test_feature_001_state_machine.py:17, 29-30, 40-41
**Quote:**

```
session = resp.json()
session_id = session["id"]
assert session["status"] == "running"

paused_session = resp.json()
assert paused_session["status"] == "paused"

completed_session = resp.json()
assert completed_session["status"] == "completed"
assert completed_session["completed_at"] is not None
```

**Read:** The test assumes Session responses include fields: id, status, completed_at. In test_pause_duration_accumulation, it also assumes: session_length_ms (line 60), paused_duration_ms (lines 65, 76, 83, 88).
**Concern:** The contract note (contract-note-003) specifies the Session table schema (status enum, session_length_minutes, paused_duration_ms) but the tests use both millisecond and minute units inconsistently. test_invalid_state_transition assumes session_length_ms exists; test_pause_duration_accumulation later uses the same field name. The tests do not cite the contract note or confirm these field names against it. When the Tweedles implement the backend, they'll be choosing field names based on this test, which means field naming will be driven by the test, not by the contract.
**Request:** Normalize field names across all tests. Decide: does the backend return session_length_minutes or session_length_ms? The contract says the table stores session_length_minutes; the tests should ask for that. Pick one unit (I'd recommend milliseconds for internal storage, but confirm with contract-note-003's intent). Add a comment citing the contract note so the Tweedles know where the schema comes from. Example: '# Per contract-note-003, Session.session_length_minutes is captured at creation time.'

#### change-required: Missing field: SessionRecord response shape undefined
**Location:** tests/test_feature_001_state_machine.py:48-52
**Quote:**

```
resp = client.get("/api/session-history/all-time")
assert resp.status_code == 200
records = resp.json()
assert len(records) > 0, "SessionRecord should be appended on completion"

matching_records = [r for r in records if r.get("completed_at") == completed_session["completed_at"]]
```

**Read:** The test queries /api/session-history/all-time and expects a list of records with fields: completed_at, session_type, session_duration_minutes. But the test doesn't verify the shape of the response. It's unclear whether the API returns individual SessionRecord objects, aggregated summaries, or something else.
**Concern:** The test matches records by completed_at, but doesn't verify uniqueness or ordering. If two sessions happened to complete at the exact same second, the match would be ambiguous. More importantly, if /api/session-history/all-time returns aggregated data (per the feature spec), it wouldn't have a completed_at field per record—it would have date fields and aggregated counts. This test seems to assume it returns raw SessionRecords, not aggregated summaries.
**Request:** Clarify the shape of /api/session-history/all-time. Does it return: (a) a list of individual SessionRecord objects, or (b) aggregated summaries grouped by date (per feature-003 contract)? The test currently assumes (a), but feature-003 seems to be asking for (b). If (a), the test should verify uniqueness by checking that matched_records has exactly 1 element. If (b), the test needs to be rewritten. I'd suggest matching by session_id instead of completed_at to avoid ambiguity.

#### change-required: test_pause_duration_accumulation makes an unverified assumption about how pause time is tracked
**Location:** tests/test_feature_001_state_machine.py:60-88
**Quote:**

```
first_pause_duration = paused_session_1.get("paused_duration_ms", 0)
...
assert resumed_session.get("paused_duration_ms", 0) == first_pause_duration, "Pause duration should persist after resume"
```

**Read:** The test assumes that when a session is paused, the response includes a paused_duration_ms field that gets populated by the backend. It then verifies this field persists across resume. Later, it checks that the accumulated pause duration is subtracted from the session duration.
**Concern:** The contract note says 'paused_duration_ms incremented atomically' and 'tracks cumulative pause time across the session.' The test assumes the frontend can read this value from the Session response. But the test doesn't verify that the pause was actually timed by the backend (i.e., that paused_duration_ms reflects actual elapsed time during the pause). The test uses .get(..., 0), which means it gracefully handles a missing field by defaulting to 0. This allows a broken implementation (one that never sets paused_duration_ms) to pass the test as long as the field is missing. I'd argue this is a test bug—the test should assert the field exists and has the expected value, not silently default to 0.
**Request:** Change all .get("paused_duration_ms", 0) to direct dictionary access: paused_session["paused_duration_ms"]. This will fail loudly if the field is missing, making the test's expectation explicit. Similarly, change session.get("session_length_ms", 25 * 60 * 1000) to session["session_length_ms"] so the test is clear about what fields must exist. If defaults are necessary, explain in a comment why (e.g., 'feature-004 allows customizing session length; if not set, default to 25 min').

#### change-required: test_pause_duration_accumulation doesn't test actual pause timing
**Location:** tests/test_feature_001_state_machine.py:75-76
**Quote:**

```
# Pause after ~5 minutes
resp = client.post(f"/api/session/{session_id}/pause")
assert resp.status_code == 200
paused_session_1 = resp.json()
assert paused_session_1.get("paused_duration_ms", 0) > 0
```

**Read:** The test pauses immediately after starting and asserts paused_duration_ms > 0. But there's no actual elapsed time—the pause is called immediately. The assertion that paused_duration_ms > 0 will fail if the backend correctly tracks pause duration starting from the moment pause is called (which would be milliseconds, not seconds).
**Concern:** The test has a timing assumption that doesn't match reality. When pause is called immediately after session start, the paused_duration_ms should be ~0 (or very small, microseconds). The comment '# Pause after ~5 minutes' suggests the test author intended to wait 5 minutes, but the code doesn't do that. This test will fail because the backend will report a very small pause duration, not a meaningful one.
**Request:** Either (1) add actual delays (sleep) between start/pause/resume to make the timing realistic, or (2) rewrite the test to not care about the actual duration—just verify that pause duration is tracked and accumulated across multiple pause/resume cycles. Option (2) is better for a unit test that shouldn't depend on timing. Example: 'After pause, paused_duration_ms should be > 0. After resume and pause again, paused_duration_ms should increase.' Separate integration tests can verify actual timing accuracy.

#### suggestion: test_pause_duration_accumulation: Tolerance range is arbitrary
**Location:** tests/test_feature_001_state_machine.py:88-90
**Quote:**

```
assert abs(recorded_duration_ms - expected_duration_ms) < 5000, \
    f"Recorded duration {recorded_duration_ms}ms should account for accumulated pause {second_pause_duration}ms"
```

**Read:** The test allows a 5-second tolerance when comparing expected vs. recorded duration. This is reasonable for an integration test where timing can drift, but the tolerance should be justified and consistent.
**Concern:** A 5-second tolerance is large. If the session is 25 minutes, that's a 0.3% error margin, which is reasonable. But the test doesn't explain where this number comes from. The contract note says 'within one second,' but this test allows five. This could mask bugs where pause duration accumulation is off by more than a second.
**Request:** Document why 5 seconds is acceptable. If the contract says 'within one second,' change the tolerance to 1000ms. If 5 seconds is intentional (e.g., to account for test framework overhead), add a comment explaining this.

#### change-required: test_feature_002_today_count.py: test_empty_count doesn't verify the actual value is numeric
**Location:** tests/test_feature_002_today_count.py:47-53
**Quote:**

```
assert count_response["count"] == 0, "Count should be 0 when no sessions completed"
assert count_response["total_focus_minutes"] == 0, "Total minutes should be 0 when no sessions completed"
```

**Read:** The test asserts count == 0 and total_focus_minutes == 0, but doesn't verify that these are numeric values, not strings or other types.
**Concern:** Frontend type safety depends on these being integers. A sloppy implementation might return {"count": "0", "total_focus_minutes": "0"} (strings), and the test would fail because "0" != 0 in Python. But a more dangerous scenario: if the endpoint is broken and returns null or omits the field, the test would fail with a KeyError, not a type assertion. The contract note says 'count and total_focus_minutes are numeric integers' but this test doesn't enforce that.
**Request:** Add explicit type checks: `assert isinstance(count_response["count"], int)` and `assert isinstance(count_response["total_focus_minutes"], int)`. This ensures the field is a number, not a string that happens to compare equal to 0.

#### suggestion: test_multi_session_aggregation: Timing assumption about session duration
**Location:** tests/test_feature_002_today_count.py:62-74
**Quote:**

```
# Complete 3 sessions
for _ in range(3):
    resp = client.post("/api/session/start")
    assert resp.status_code == 200
    session = resp.json()
    
    resp = client.post(f"/api/session/{session['id']}/complete")
    assert resp.status_code == 200
```

**Read:** The test starts and immediately completes sessions (no elapsed time). It then asserts total_focus_minutes > 0. But if there's no elapsed time, total_focus_minutes would be 0 or very small (milliseconds).
**Concern:** Similar to the pause_duration_accumulation test, this test has a timing assumption that doesn't match the code. When a session is completed immediately after starting, the session_duration_ms (or total_focus_minutes) would be ~0, not > 0. The test will likely fail.
**Request:** Either add actual elapsed time (mocking or real delays) or change the assertion to just verify that count == 3 without checking total_focus_minutes. The feature contract says 'review today's session activity at a glance'—the count is the main requirement, not the exact duration. For unit tests, count correctness is sufficient. Duration accumulation should be tested in integration tests with real timing.

#### note: Tests reference endpoints that don't have defined schemas
**Location:** tests/test_feature_001_state_machine.py and tests/test_feature_002_today_count.py throughout
**Quote:**

```
/api/session/start, /api/session/{session_id}/pause, /api/session/{session_id}/complete, /api/session/{session_id}/resume, /api/session-history/all-time, /api/session-counts/today
```

**Read:** The tests reference six endpoints with no defined response schemas. Contract notes describe the persistence layer but not the API contracts.
**Concern:** The Tweedles will need to know: for each endpoint, what is the request body shape (if any), what is the response shape, what are the error responses? The contract notes should spell this out, or the tests should be more explicit about what they expect. Right now, the Tweedles are guessing based on test code.
**Request:** This is not a test code issue per se—it's a downstream issue for the Tweedles. But before the Tweedles start implementing, confirm that each endpoint has a clear contract. Ideally, add OpenAPI documentation or write out the contracts explicitly in the ticket. For now, the tests are a useful starting point, but they should be supplemented with explicit endpoint docs.

### Approvals

- Test organization is clear: Feature 001 lifecycle and state machine are in separate files, making it easy to find tests for a specific aspect.
- Scenario naming is specific: 'test_invalid_state_transition' and 'test_pause_duration_accumulation' are clear about what they test, not vague like 'test_session' or 'test_behavior'.
- The majority of test_feature_001_session_lifecycle.py and test_feature_001_failure_modes.py are properly skipped with pytest.skip() and informative TODOs, which is appropriate for future work.
- Comments in test_feature_001_state_machine.py are detailed and explain the intent of each test, not just the mechanics. For example, 'Invalid transitions like paused→paused or completed→running are rejected' tells the reader what invariant is being protected.

### Cross-domain references

- The pause duration accumulation test (test_pause_duration_accumulation) involves timing and state transitions. The contract note describes the state machine; the test verifies it. This is a good alignment between architecture and tests.
- Endpoint response schemas are referenced but not formally specified. The Cat should ensure that the ADR (adr-001) includes API contract specifications before the Tweedles start implementing.
