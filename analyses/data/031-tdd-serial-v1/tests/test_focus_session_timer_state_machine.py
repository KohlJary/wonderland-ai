"""
State machine edge cases for focus session timer (feature 001).

Tests the pause/resume/skip atomicity and state-transition rules that the
contract specifies. These tests verify that the session state object correctly
enforces its state machine.

These tests will fail until M5 implementation ships the Session model.
"""

import pytest


class TestFocusSessionStateTransitions:
    """Session state machine must enforce valid transitions."""

    def test_cannot_pause_non_running_session(self, client):
        """Pause on a completed or paused session should fail gracefully."""
        # Start and pause
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        client.post(f"/api/sessions/{session_id}/pause")
        
        # Try to pause again
        response = client.post(f"/api/sessions/{session_id}/pause")
        # Either 400 (bad request, already paused) or idempotent 200 is acceptable.
        # Contract should clarify; for now, we accept either.
        assert response.status_code in [200, 400]

    def test_cannot_resume_non_paused_session(self, client):
        """Resume on a running or completed session should fail or be idempotent."""
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Try to resume a running session
        response = client.post(f"/api/sessions/{session_id}/resume")
        assert response.status_code in [200, 400]

    def test_skip_from_paused_state(self, client):
        """Skip should work from paused state, transitioning to completed."""
        # Start and pause
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        client.post(f"/api/sessions/{session_id}/pause")
        
        # Skip from paused state
        response = client.post(f"/api/sessions/{session_id}/skip")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completion_type"] == "skip"

    def test_cannot_skip_completed_session(self, client):
        """Skip on already-completed session should fail or be idempotent."""
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Skip once
        client.post(f"/api/sessions/{session_id}/skip")
        
        # Try to skip again
        response = client.post(f"/api/sessions/{session_id}/skip")
        assert response.status_code in [200, 400]

    def test_pause_resume_elapsed_accumulation(self, client):
        """
        Multiple pause/resume cycles must accumulate elapsed correctly.
        
        Scenario: start -> pause after E1 ms -> resume -> pause after E1+E2 ms 
        -> resume. Final elapsed must be E1+E2, not E1 or E2.
        """
        pytest.skip("Requires time control in backend (mocking or test endpoint); not available yet")
        # When M5 adds a test endpoint to advance session time, implement this.

    def test_pause_prevents_auto_completion(self, client):
        """While paused, elapsed time does not advance toward completion."""
        pytest.skip("Requires time mocking in backend")
        # When paused, if we wait 1 hour, elapsed must still be whatever it was at pause.

    def test_session_not_callable_if_never_started(self, client):
        """Fetching a non-existent session should 404."""
        response = client.get("/api/sessions/nonexistent-id")
        assert response.status_code == 404


class TestFocusSessionCompletionSemantics:
    """Completion type and event recording."""

    def test_completion_type_is_timeout_on_natural_completion(self, client):
        """When timer naturally expires, completion_type='timeout'."""
        pytest.skip("Requires time control in backend")
        # Start a 1-second timer, let it expire, verify completion_type='timeout'

    def test_completion_type_is_skip_on_manual_skip(self, client):
        """When user skips, completion_type='skip'."""
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        response = client.post(f"/api/sessions/{session_id}/skip")
        assert response.json()["completion_type"] == "skip"

    def test_completed_session_has_timestamp(self, client):
        """Completed session must record when completion occurred."""
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        response = client.post(f"/api/sessions/{session_id}/skip")
        data = response.json()
        assert "completed_at" in data or "timestamp" in data
