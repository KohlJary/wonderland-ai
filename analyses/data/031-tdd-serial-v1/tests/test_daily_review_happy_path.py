"""
Happy-path scenarios for daily session review (feature 003).

Tests the core user journey: David completes focus and break sessions,
then views a daily summary showing counts and total time.

These tests will fail until M5 implementation ships the event logging
and daily-review query API.
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestDailyReviewHappyPath:
    """Core user journey for daily session review."""

    def test_daily_review_endpoint_exists(self, client):
        """GET /api/daily-review?date=YYYY-MM-DD returns a status 200."""
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        
        # Endpoint must exist and return 200 even if no sessions today
        assert response.status_code == 200
        data = response.json()
        assert "date" in data

    def test_empty_day_returns_zero_counts(self, client):
        """
        On a day with no sessions, daily review returns all counts as 0,
        not NULL or undefined.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["completed_focus_count"] == 0
        assert data["completed_break_count"] == 0
        assert data["skipped_break_count"] == 0
        assert data["total_focus_time_ms"] == 0

    def test_daily_review_structure_has_required_fields(self, client):
        """
        Daily review response must include: completed_focus_count,
        completed_break_count, skipped_break_count, total_focus_time_ms.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        
        data = response.json()
        required_fields = [
            "completed_focus_count",
            "completed_break_count",
            "skipped_break_count",
            "total_focus_time_ms",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_log_session_completion_endpoint_exists(self, client):
        """
        POST /api/sessions/<id>/complete logs a session completion to the event log.
        """
        # First, start a session (from feature 001)
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        assert start_resp.status_code == 201
        session_id = start_resp.json()["session_id"]
        
        # Log completion (new endpoint for feature 003)
        response = client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        assert response.status_code in [200, 201]

    def test_completed_sessions_appear_in_daily_review(self, client):
        """
        After a focus session is logged as completed, daily review counts it.
        """
        # Start a session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        
        # Log completion (25 min = 1,500,000 ms)
        client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        # Check daily review
        today = datetime.now(timezone.utc).date().isoformat()
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 1
        assert data["total_focus_time_ms"] == 1500000

    def test_multiple_sessions_sum_correctly(self, client):
        """
        Multiple sessions: counts add up, total time is the sum.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Log 3 focus sessions: 25 min, 25 min, 30 min
        for duration_ms in [1500000, 1500000, 1800000]:
            start_resp = client.post("/api/sessions/start", json={"duration_seconds": duration_ms // 1000})
            session_id = start_resp.json()["session_id"]
            client.post(
                f"/api/sessions/{session_id}/complete",
                json={"type": "focus", "duration_ms": duration_ms}
            )
        
        # Check daily review
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 3
        assert data["total_focus_time_ms"] == 1500000 + 1500000 + 1800000

    def test_completed_break_logged_separately(self, client):
        """
        Completed breaks are logged with type='break' and status='completed'.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Log 1 focus session
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 25 * 60})
        session_id = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{session_id}/complete",
            json={"type": "focus", "duration_ms": 1500000}
        )
        
        # Log 1 completed break
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        break_session_id = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{break_session_id}/complete",
            json={"type": "break", "status": "completed", "duration_ms": 300000}
        )
        
        # Check daily review
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_focus_count"] == 1
        assert data["completed_break_count"] == 1
        assert data["total_focus_time_ms"] == 1500000  # breaks don't count toward focus time

    def test_skipped_break_logged_separately(self, client):
        """
        Skipped breaks are logged with type='break' and status='skipped'.
        """
        today = datetime.now(timezone.utc).date().isoformat()
        
        # Log 1 completed break
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        break_id_1 = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{break_id_1}/complete",
            json={"type": "break", "status": "completed", "duration_ms": 300000}
        )
        
        # Log 1 skipped break
        start_resp = client.post("/api/sessions/start", json={"duration_seconds": 5 * 60})
        break_id_2 = start_resp.json()["session_id"]
        client.post(
            f"/api/sessions/{break_id_2}/complete",
            json={"type": "break", "status": "skipped", "duration_ms": 0}
        )
        
        # Check daily review
        response = client.get(f"/api/daily-review?date={today}")
        data = response.json()
        
        assert data["completed_break_count"] == 1
        assert data["skipped_break_count"] == 1

    def test_daily_review_excludes_future_sessions(self, client):
        """
        Daily review for today only includes sessions completed today,
        not sessions completed on other dates.
        """
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        
        # This test will need backend support for backdating session completions.
        pytest.skip("Requires backend test endpoint to fake session timestamps")
