"""
Fragility and edge cases for daily session review (feature 003).

These tests probe failure modes:
- Duplicate session logging (idempotency)
- Timezone boundary crossing
- Event log schema correctness
- Empty day handling
- Paused/resumed session classification
- Malformed input validation
- Concurrent completion logging
- Date parameter validation

These tests will fail until M5 implementation ships event logging
with proper deduplication, timezone handling, aggregation, and input validation.
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestEventLogDeduplication:
    """Session completion must be idempotent: logging the same session twice
    must result in exactly one entry in the event log."""

    def test_duplicate_session_completion_not_double_counted(self, client):
        """
        If POST /api/sessions/<id>/complete is called twice with identical
        payload, the daily review must count the session only once.
        
        This tests idempotency: the second POST is a retry of the first,
        and should not increase the count.
        """
        # Start and complete a session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # First completion
        resp1 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        assert resp1.status_code in [200, 201]
        
        # Retry: second completion (same payload)
        resp2 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        # Both should succeed (or second should be idempotent 200)
        assert resp2.status_code in [200, 201]
        
        # Daily review must count only 1 session, not 2
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 1
        assert data["total_focus_time_ms"] == 1500000

    def test_event_log_unique_constraint_on_session_id(self, client):
        """
        The event log must enforce uniqueness: same session_id cannot
        appear twice, even if the completion type/duration differs.
        """
        # Start a session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # First completion with duration_ms=1500000
        resp1 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        assert resp1.status_code in [200, 201]
        
        # Second completion with different duration (simulating conflicting retry)
        resp2 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1400000}
        )
        
        # Backend must reject the duplicate or handle it idempotently
        # (either 409 Conflict or 200 OK with same result)
        assert resp2.status_code in [200, 201, 409]
        
        # Daily review must reflect one entry, with the first duration
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        # Should show 1 session with 1500000 ms (first completion wins)
        assert data["completed_focus_count"] == 1
        assert data["total_focus_time_ms"] == 1500000


class TestTimezoneBoundaryCrossing:
    """Sessions completing across midnight in the user's timezone
    must belong to the correct date in daily review."""

    def test_session_completing_after_midnight_belongs_to_new_day(self, client):
        """
        A session that completes after midnight belongs to the next day's
        daily review, not the previous day's, even if it started before midnight.
        
        This requires the backend to record completion_time separately from
        start_time, and to query by completion_time, not start_time.
        """
        pytest.skip(
            "Requires backend test endpoint to mock time / backdated completions. "
            "The contract must clarify: does query use completion_time or start_time?"
        )

    def test_daily_review_respects_user_timezone_not_utc(self, client):
        """
        A user in Pacific Time (UTC-8) should see their midnight boundary
        at 8am UTC, not midnight UTC.
        
        Example: 11:59pm PT on Monday = 7:59am UTC on Tuesday. A session
        completing at 12:05am PT (8:05am UTC) should belong to Tuesday's
        PT review, not Monday's UTC review.
        """
        pytest.skip(
            "Requires frontend to send user_timezone in request, and backend to use it. "
            "Test depends on contract clarification about timezone handling."
        )

    def test_daily_review_date_parameter_is_interpreted_in_user_tz(self, client):
        """
        When frontend requests GET /api/daily-review?date=2024-01-15&timezone=America/Los_Angeles,
        the 'date' parameter is interpreted as that day in the user's timezone,
        not as UTC.
        """
        pytest.skip(
            "Depends on frontend implementation of timezone parameter. "
            "Contract must define the parameter name and format."
        )


class TestSessionTypeAndStatusClassification:
    """Focus vs. break vs. skipped must be correctly distinguished
    so daily review counts are meaningful."""

    def test_break_session_must_have_status_completed_or_skipped(self, client):
        """
        Break completions must include a status field that distinguishes
        'completed' from 'skipped'. If status is missing, daily review
        cannot compute break adherence.
        """
        # Start and skip a break
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        break_id = start_resp.json()["session_id"]
        
        # Log with status='skipped'
        resp = client.post(
            f"/api/sessions/{break_id}/complete",
            json={"type": "break", "status": "skipped"}
        )
        
        assert resp.status_code in [200, 201]
        
        # Daily review must count it as skipped, not completed
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["skipped_break_count"] == 1
        assert data["completed_break_count"] == 0

    def test_focus_session_and_break_session_have_separate_counts(self, client):
        """
        Focus sessions and break sessions must be counted separately.
        'completed_break_count' should only include breaks, not focus sessions.
        """
        # Log 1 focus session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        focus_id = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{focus_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        # Log 1 break session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        break_id = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{break_id}/complete",
            json={"type": "break", "status": "completed", "duration_ms": 300000}
        )
        
        # Daily review must show 1 focus, 1 break
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 1
        assert data["completed_break_count"] == 1
        assert data["total_focus_time_ms"] == 1500000  # breaks don't contribute

    def test_skipped_breaks_must_be_logged_not_silent(self, client):
        """
        When a user skips a break, the event log must record it.
        If skipped breaks are silent (not logged), daily review will show
        wrong break adherence (missing the skip).
        """
        # Log 2 breaks: 1 completed, 1 skipped
        # Completed
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        id1 = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{id1}/complete",
            json={"type": "break", "status": "completed", "duration_ms": 300000}
        )
        
        # Skipped
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        id2 = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{id2}/complete",
            json={"type": "break", "status": "skipped", "duration_ms": 0}
        )
        
        # Daily review must show both
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        # Total breaks = 2 (one completed, one skipped)
        total_breaks = data["completed_break_count"] + data["skipped_break_count"]
        assert total_breaks == 2


class TestAggregationEdgeCases:
    """SUM and COUNT aggregation must handle edge cases correctly."""

    def test_sum_of_durations_with_no_sessions_returns_zero_not_null(self, client):
        """
        If no sessions are completed, total_focus_time_ms must be 0,
        not NULL. NULL is a JSON encoding error and breaks frontend display.
        """
        # Pick a date with no sessions
        future_date = (datetime.now(timezone.utc).date() + timedelta(days=100)).isoformat()
        
        response = client.get(f"/api/daily-review?date={future_date}")
        data = response.json()
        
        assert data["total_focus_time_ms"] == 0
        assert data["total_focus_time_ms"] is not None

    def test_count_of_sessions_with_none_returns_zero_not_null(self, client):
        """
        If no focus sessions are completed, completed_focus_count must be 0,
        not NULL or undefined.
        """
        future_date = (datetime.now(timezone.utc).date() + timedelta(days=100)).isoformat()
        
        response = client.get(f"/api/daily-review?date={future_date}")
        data = response.json()
        
        assert data["completed_focus_count"] == 0
        assert data["completed_focus_count"] is not None


class TestPauseAndResumeClassification:
    """When a session is paused and resumed, does it count as 'completed'?
    The story confusion flag raises this; the contract must clarify."""

    def test_paused_then_completed_session_counts_as_completed(self, client):
        """
        A session that is paused, then resumed, then completes normally
        should be counted as 1 completed session.
        
        This assumes: "completed" means the timer reached zero, regardless
        of pause/resume history.
        """
        pytest.skip(
            "Depends on contract clarification: what counts as 'completed'? "
            "Is a paused session 'completed' when resumed? "
            "This is a story/product decision (Alice/Rabbit), not a test-surface decision."
        )

    def test_session_status_state_machine_is_documented(self, client):
        """
        The session state machine (running, paused, completed, skipped)
        must be documented so tests can verify correct transitions.
        """
        pytest.skip(
            "Requires contract note that defines valid session.status values. "
            "Once defined, add tests for each state transition."
        )


class TestMalformedInputValidation:
    """Backend must gracefully reject malformed completion payloads."""

    def test_missing_type_field_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete without 'type' field must return 400 Bad Request,
        not crash or silently accept invalid data.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Missing 'type' field
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"duration_ms": 1500000}
        )
        
        assert resp.status_code == 400

    def test_invalid_type_value_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete with invalid type (not 'focus' or 'break')
        must return 400 Bad Request.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Invalid type
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "sleep", "duration_ms": 1500000}
        )
        
        assert resp.status_code == 400

    def test_missing_duration_ms_for_focus_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete for focus type without duration_ms must return 400.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Missing duration_ms
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus"}
        )
        
        assert resp.status_code == 400

    def test_negative_duration_ms_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete with negative duration_ms must return 400.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Negative duration
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": -1000}
        )
        
        assert resp.status_code == 400

    def test_duration_ms_not_integer_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete with non-integer duration_ms must return 400.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # String duration
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": "1500000"}
        )
        
        assert resp.status_code == 400

    def test_missing_status_for_break_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete for break type without status field must return 400.
        Break status must be explicitly 'completed' or 'skipped'.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Break missing status
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "break", "duration_ms": 300000}
        )
        
        assert resp.status_code == 400

    def test_invalid_break_status_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete for break with invalid status must return 400.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Invalid status
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "break", "status": "maybe_later", "duration_ms": 0}
        )
        
        assert resp.status_code == 400

    def test_invalid_session_id_format_returns_400(self, client):
        """
        POST /api/sessions/{id}/complete with invalid UUID format must return 400 or 404.
        """
        resp = client.post(
            f"/api/sessions/not-a-uuid/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        assert resp.status_code in [400, 404]

    def test_nonexistent_session_id_returns_404(self, client):
        """
        POST /api/sessions/{id}/complete for a session_id that doesn't exist must return 404.
        """
        import uuid
        fake_id = str(uuid.uuid4())
        
        resp = client.post(
            f"/api/sessions/{fake_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        assert resp.status_code == 404


class TestConcurrentSessionLogging:
    """Multiple clients logging the same session simultaneously must not corrupt state."""

    def test_concurrent_completion_requests_for_same_session_result_in_single_log(self, client):
        """
        If two requests arrive concurrently attempting to log the same session_id,
        the event log must contain only one entry (not two), with the invariant:
        each session_id appears exactly once.
        
        This tests that the backend's unique constraint on session_id prevents
        race-condition duplicates at the database level.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Simulate concurrent requests by making two synchronous calls in quick succession.
        # In a real distributed system, these would be truly concurrent; here we're testing
        # that the backend's deduplication logic catches them.
        resp1 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        resp2 = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        # Both requests should succeed (200/201), but the second may be idempotent (200)
        assert resp1.status_code in [200, 201]
        assert resp2.status_code in [200, 201]
        
        # Daily review must show only 1 session, not 2
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 1
        assert data["total_focus_time_ms"] == 1500000


class TestDateParameterValidation:
    """Daily review date parameter must accept valid dates and reject invalid ones."""

    def test_invalid_date_format_returns_400(self, client):
        """
        GET /api/daily-review?date=not-a-date must return 400 Bad Request.
        """
        resp = client.get("/api/daily-review?date=not-a-date")
        
        assert resp.status_code == 400

    def test_malformed_date_like_2024_13_01_returns_400(self, client):
        """
        GET /api/daily-review?date=2024-13-01 (invalid month) must return 400.
        """
        resp = client.get("/api/daily-review?date=2024-13-01")
        
        assert resp.status_code == 400

    def test_nonexistent_date_like_2024_02_30_returns_400(self, client):
        """
        GET /api/daily-review?date=2024-02-30 (nonexistent day) must return 400.
        """
        resp = client.get("/api/daily-review?date=2024-02-30")
        
        assert resp.status_code == 400

    def test_valid_leap_day_returns_200(self, client):
        """
        GET /api/daily-review?date=2024-02-29 (valid leap day) must return 200.
        2024 is a leap year; Feb 29 is valid.
        """
        resp = client.get("/api/daily-review?date=2024-02-29")
        
        assert resp.status_code == 200

    def test_valid_past_date_returns_200(self, client):
        """
        GET /api/daily-review?date=2020-01-01 (past date) must return 200,
        with empty counts if no sessions logged that day.
        """
        resp = client.get("/api/daily-review?date=2020-01-01")
        
        assert resp.status_code == 200
        data = resp.json()
        assert "completed_focus_count" in data

    def test_valid_future_date_returns_200(self, client):
        """
        GET /api/daily-review?date=2099-12-31 (future date) must return 200,
        with empty counts.
        """
        resp = client.get("/api/daily-review?date=2099-12-31")
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["completed_focus_count"] == 0

    def test_missing_date_parameter_returns_400_or_uses_default(self, client):
        """
        GET /api/daily-review (without date parameter) should either:
        - Return 400 Bad Request (requires parameter), or
        - Default to today's date and return 200.
        
        The contract must clarify which behavior is intended.
        """
        resp = client.get("/api/daily-review")
        
        # Accept either behavior; the contract decides.
        assert resp.status_code in [200, 400]


class TestLargeNumberHandling:
    """Aggregation must handle large duration values correctly."""

    def test_large_duration_does_not_overflow_aggregation(self, client):
        """
        A single session with very large duration_ms (e.g., 999999999 ms, ~11.5 days)
        must not cause integer overflow in the total_focus_time_ms aggregation.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 999999})
        session_id = start_resp.json()["session_id"]
        
        # Log a very large duration (999999999 ms = ~11.5 days)
        large_duration_ms = 999999999
        resp = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": large_duration_ms}
        )
        
        assert resp.status_code in [200, 201]
        
        # Daily review must correctly sum the large duration
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["total_focus_time_ms"] == large_duration_ms

    def test_many_sessions_do_not_overflow_count_aggregation(self, client):
        """
        Logging many sessions (100+) must not cause integer overflow in count aggregation.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Log 100 focus sessions
        for _ in range(100):
            start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
            session_id = start_resp.json()["session_id"]
            client.post(
                f"/api/sessions/{session_id}/complete",
                json={"type": "focus", "duration_ms": 1500000}
            )
        
        # Daily review must show exactly 100
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 100
        assert data["total_focus_time_ms"] == 100 * 1500000
