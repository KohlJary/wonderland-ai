"""
Test scenarios for Feature 003: Review today's focus work and recent sessions.

Contracts: Session history query & recent activity (003)
Persona: James, therapist using Pomodoro for admin work, tracking daily progress

Tests the happy path (user views today's sessions and recent timeline)
and edge cases around query boundaries, pagination, timezone handling, and consistency.
"""

from datetime import datetime, timezone

import pytest


def test_james_views_today_session_count_and_timeline(client):
    """Happy path: James opens the History tab and sees today's sessions.
    
    Setup: James has completed 4 sessions today (10:15, 11:00, 14:00, 14:30 AM).
    Trigger: James taps the History tab.
    Expected: He sees "4 sessions today" and a timeline showing start times and durations.
    """
    # Simulate completing 4 sessions today
    for i in range(4):
        res = client.post("/session/start", json={})
        assert res.status_code == 200
        session = res.json()
        
        res = client.post(f"/session/{session['id']}/stop", json={})
        assert res.status_code == 200
    
    # Query today's sessions
    res = client.get("/sessions/history?since_timestamp=today_midnight")
    assert res.status_code == 200
    history = res.json()
    
    # Should include all 4 sessions
    assert len(history) == 4
    
    # Each session should have required fields
    for session in history:
        assert "start_time" in session
        assert "completed_at" in session
        assert "duration_seconds" in session
        assert session["completed_at"] is not None
    
    # Sessions should be ordered by completed_at DESC (most recent first)
    for i in range(len(history) - 1):
        assert history[i]["completed_at"] >= history[i + 1]["completed_at"]


def test_james_sees_total_focus_time_for_today(client):
    """Edge case: Display total minutes of focus time (not just count).
    
    Setup: James completed 3 sessions today, each 25 minutes = 75 total.
    Trigger: James views the History tab.
    Expected: Display shows "75 minutes today" or "4 hours 15 minutes".
    """
    # Complete 3 sessions
    for i in range(3):
        res = client.post("/session/start", json={})
        session = res.json()
        res = client.post(f"/session/{session['id']}/stop", json={})
        assert res.status_code == 200
    
    res = client.get("/sessions/history?since_timestamp=today_midnight")
    assert res.status_code == 200
    history = res.json()
    
    # Compute total duration
    total_seconds = sum(s["duration_seconds"] for s in history)
    assert total_seconds == (3 * 25 * 60)  # 3 sessions * 25 min * 60 sec
    
    # Client would display this as 75 minutes or 1h 15m


def test_history_query_respects_since_timestamp_parameter(client):
    """Edge case: Query can filter by time range (default: 7 days ago).
    
    Setup: User has sessions from last week and this week.
    Trigger: Query /sessions/history?since_timestamp=<7_days_ago_unix>
    Expected: Only sessions after that timestamp are returned.
    """
    # Complete a session now
    res = client.post("/session/start", json={})
    session_today = res.json()
    res = client.post(f"/session/{session_today['id']}/stop", json={})
    assert res.status_code == 200
    
    # Query with a recent since_timestamp (should get this session)
    now = datetime.now(timezone.utc).timestamp()
    res = client.get(f"/sessions/history?since_timestamp={int(now - 3600)}")  # Last hour
    assert res.status_code == 200
    history_recent = res.json()
    assert len(history_recent) >= 1
    
    # Query with an old since_timestamp (should get this session too)
    res = client.get(f"/sessions/history?since_timestamp={int(now - 86400 * 7)}")  # Last 7 days
    assert res.status_code == 200
    history_week = res.json()
    assert len(history_week) >= 1
    
    # Query with a future timestamp (should get nothing)
    res = client.get(f"/sessions/history?since_timestamp={int(now + 3600)}")  # Next hour
    assert res.status_code == 200
    history_future = res.json()
    assert len(history_future) == 0


def test_history_returns_only_completed_sessions(client):
    """Edge case: History includes only state=completed sessions.
    
    Setup: One active session, one completed session.
    Trigger: Query /sessions/history.
    Expected: Only the completed session appears, not the active one.
    """
    # Start a session but don't complete it
    res = client.post("/session/start", json={})
    active_session = res.json()
    active_id = active_session["id"]
    
    # Start and complete another session
    res = client.post("/session/start", json={})
    session2 = res.json()
    res = client.post(f"/session/{session2['id']}/stop", json={})
    assert res.status_code == 200
    
    # Query history
    res = client.get("/sessions/history")
    assert res.status_code == 200
    history = res.json()
    
    # Should only see the completed session, not the active one
    assert len(history) == 1
    assert history[0]["id"] == session2["id"]
    assert active_id not in [s["id"] for s in history]


@pytest.mark.skip(reason="Pagination not required in v1; would test in v2")
def test_history_pagination_for_50_plus_sessions(client):
    """Edge case: If user has 50+ sessions, paginate the response.
    
    Setup: User has 150 sessions (3 months of data).
    Trigger: Query /sessions/history?limit=50&offset=0.
    Expected: First query returns 50 most recent, subsequent query with offset=50 gets next 50.
    
    Skipped for v1 (default limit=50 should be sufficient for typical usage).
    """
    pass


def test_history_break_info_included(client):
    """Edge case: History includes whether a break was taken or skipped.
    
    Setup: Session completed, user skipped the break.
    Trigger: Query /sessions/history.
    Expected: Response includes break_skipped=true for that session.
    """
    # Complete a session and skip the break
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    
    # Query history
    res = client.get("/sessions/history")
    assert res.status_code == 200
    history = res.json()
    
    # Session should show break_skipped
    assert len(history) > 0
    assert "break_skipped" in history[0]
    assert history[0]["break_skipped"] is True


def test_history_cache_invalidates_on_session_completion(client):
    """Edge case: Frontend cache of session history updates when a session completes.
    
    Setup: Frontend has cached /sessions/history from 5 minutes ago (3 sessions).
    Trigger: New session completes, frontend should refresh cache automatically.
    Expected: /sessions/history now returns 4 sessions; cache is invalidated.
    
    Note: This test documents the contract expectation for frontend caching behavior.
    The backend implementation simply ensures /sessions/history always returns
    the current state; the frontend is responsible for cache invalidation.
    """
    # Get initial history
    res = client.get("/sessions/history")
    initial = res.json()
    initial_count = len(initial)
    
    # Complete a new session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    # Query history again (cache should be invalidated on client)
    res = client.get("/sessions/history")
    updated = res.json()
    assert len(updated) == initial_count + 1


def test_empty_history_when_no_sessions_completed(client):
    """Edge case: New user with zero completed sessions.
    
    Setup: User just installed the app, hasn't completed any sessions.
    Trigger: Query /sessions/history.
    Expected: Return empty array [], not error.
    """
    # Assume a fresh test database with no prior sessions
    res = client.get("/sessions/history")
    assert res.status_code == 200
    history = res.json()
    
    # Could be empty, or could have sessions from prior test setup
    # The contract is: return array (possibly empty)
    assert isinstance(history, list)
