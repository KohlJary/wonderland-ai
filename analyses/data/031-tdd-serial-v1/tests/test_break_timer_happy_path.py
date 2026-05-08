"""
Happy-path scenarios for break timer between sessions (feature 002).
Tests the core user journey: Marcus's focus session completes, break timer
auto-starts, he watches it count down, can skip if needed, and the flow
continues cleanly to the next focus session.

These tests will fail until M5 implementation ships the break timer logic
(auto-start on focus completion, skip mechanics, state transitions).
"""

import pytest


class TestBreakTimerAutoStart:
    """Break timer must auto-start when focus session completes."""

    def test_break_timer_auto_starts_on_focus_completion(self, client):
        """
        When a focus session reaches completion, a break session with type='break'
        must be created automatically, with status='running' and elapsed_ms=0.
        """
        # Start a focus session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        focus_session_id = start_resp.json()["session_id"]

        # Simulate focus session completion (contract: we need a way to trigger this)
        # For now, we skip and fetch to see if break exists
        skip_resp = client.post(f"/api/sessions/{focus_session_id}/skip")
        
        # After focus completes, break session should exist
        # The contract must clarify: does skip return the break session, or must we query for it?
        pytest.skip("Contract must define how auto-started break session is exposed to client")

    def test_break_session_has_same_state_shape_as_focus(self, client):
        """
        Break session uses the same Session state shape as focus sessions.
        type='break' distinguishes it, but all fields (session_id, status,
        elapsed_ms, duration_seconds, etc.) are present and consistent.
        """
        pytest.skip("Requires break session to be created; depends on auto-start contract")

    def test_break_duration_defaults_to_five_minutes(self, client):
        """
        When a break timer is auto-started, it defaults to 5 minutes
        (duration_seconds=300) unless user has customized in settings.
        """
        pytest.skip("Requires break session to be created; depends on auto-start contract")


class TestBreakTimerSkip:
    """User can skip a break, but must tap explicitly."""

    def test_skip_break_transitions_to_completed(self, client):
        """
        POST /api/sessions/<break_id>/skip immediately ends the break session.
        Status transitions to 'completed', completion_type='skip'.
        """
        pytest.skip("Requires break session to exist (auto-start contract)")

    def test_skip_break_is_idempotent(self, client):
        """
        Calling skip twice on the same break session should not double-process.
        Second call returns 409 Conflict or is silently idempotent.
        """
        pytest.skip("Requires break session to exist")

    def test_skip_break_does_not_auto_start_next_focus(self, client):
        """
        When a break is skipped, the system does NOT automatically start
        the next focus session. User must manually start a new session.
        """
        pytest.skip("Requires break session to exist")


class TestBreakTimerCompletion:
    """Break timer behavior at completion (timeout vs. skip)."""

    def test_break_completion_timeout_logs_event(self, client):
        """
        When a break completes via timeout (elapsed_ms >= duration_seconds * 1000),
        an event is logged with completion_type='timeout' for later use by
        daily review (feature 003).
        """
        pytest.skip("Requires break completion contract from feature 003")

    def test_break_completion_skip_logs_event(self, client):
        """
        When a break is skipped, an event is logged with completion_type='skip'.
        This allows feature 003 to distinguish between completed and skipped breaks.
        """
        pytest.skip("Requires break completion contract from feature 003")

    def test_break_timer_does_not_auto_resume_after_timeout(self, client):
        """
        Once a break completes (timeout or skip), it does not automatically
        resume or loop. User must manually start a new focus session.
        """
        pytest.skip("Requires break completion and state verification")


class TestBreakTimerPauseResume:
    """Pause and resume work the same for break as for focus."""

    def test_pause_break_freezes_elapsed(self, client):
        """
        POST /api/sessions/<break_id>/pause freezes the elapsed counter.
        Subsequent GETs return the same elapsed_ms value.
        """
        pytest.skip("Requires break session to exist")

    def test_resume_break_continues_from_pause_point(self, client):
        """
        POST /api/sessions/<break_id>/resume unfreezes the timer.
        elapsed_ms continues from the paused value, not from current wall time.
        """
        pytest.skip("Requires break session to exist")
