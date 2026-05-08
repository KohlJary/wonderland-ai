"""
Happy-path scenarios for focus session timer (feature 001).
Tests the core user journey: Marcus starts a timer, watches it count down, 
gets alerted at completion.

These tests will fail until M5 implementation ships the Session state model
and API endpoints.
"""

import pytest
from datetime import datetime, timezone


class TestFocusSessionTimerHappyPath:
    """Core user journey for focus session timer."""

    def test_start_focus_session_creates_active_session(self, client):
        """POST /api/sessions/start returns a session object with elapsed_ms=0."""
        response = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "elapsed_ms" in data
        assert data["elapsed_ms"] == 0
        assert data["status"] == "running"

    def test_get_active_session_shows_real_time_elapsed(self, client):
        """GET /api/sessions/<id> returns current elapsed_ms reflecting real time."""
        # Start a session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Immediately fetch — elapsed should be very small (< 100ms)
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["elapsed_ms"] < 100
        assert response.json()["status"] == "running"

    def test_focus_session_timer_display_format_mm_ss(self, client):
        """
        Session state object must provide elapsed_ms; frontend must convert 
        to MM:SS format without jitter.
        
        This tests the contract: backend provides elapsed_ms in milliseconds,
        frontend is responsible for MM:SS display calculation.
        """
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Fetch session
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify elapsed_ms exists (frontend will use this to calculate display)
        elapsed_ms = data["elapsed_ms"]
        assert isinstance(elapsed_ms, int)
        assert elapsed_ms >= 0

    def test_pause_focus_session(self, client):
        """POST /api/sessions/<id>/pause freezes elapsed counter."""
        # Start a session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Pause the session
        response = client.post(f"/api/sessions/{session_id}/pause")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        paused_elapsed = data["elapsed_ms"]
        
        # Fetch again — elapsed should NOT have advanced
        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["elapsed_ms"] == paused_elapsed

    def test_resume_focus_session(self, client):
        """POST /api/sessions/<id>/resume continues from pause point."""
        # Start
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Pause
        pause_resp = client.post(f"/api/sessions/{session_id}/pause")
        paused_elapsed = pause_resp.json()["elapsed_ms"]
        
        # Resume
        response = client.post(f"/api/sessions/{session_id}/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        assert response.json()["elapsed_ms"] == paused_elapsed

    def test_session_completion_event_on_timeout(self, client):
        """
        When a session reaches duration_seconds elapsed, status -> completed
        and completion_type = 'timeout'.
        
        This is mocked here (we don't wait 25 minutes in tests), but the
        contract must include this state transition.
        """
        pytest.skip("Cannot easily test real timeout without mocking time; tested via completion endpoint")
        # In M5 implementation, the Tweedles will provide a way to 
        # fast-forward time or manually trigger completion for testing.

    def test_session_completion_event_on_skip(self, client):
        """POST /api/sessions/<id>/skip immediately ends session."""
        # Start
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Skip
        response = client.post(f"/api/sessions/{session_id}/skip")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completion_type"] == "skip"

    def test_focus_session_completion_triggers_event_logging(self, client):
        """
        When a session completes (via timeout or skip), an event is logged
        for later consumption by daily review (feature 003).
        
        Minimal test: session completion POSTs to /api/sessions/<id>/complete
        or similar, and the event is persisted.
        """
        pytest.skip("Event logging contract defined in feature 003; tested there")
        # The contract note says "Session completion triggers event logging"
        # but doesn't specify the exact mechanism. Feature 003 will define it.
