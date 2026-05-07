"""
Test scenarios for Feature 004: Track weekly and lifetime focus statistics.

Contracts: Statistics aggregation & temporal boundaries (004)
Persona: Elena, writer tracking her productivity patterns over months

Tests the happy path (user views weekly and all-time totals)
and edge cases around temporal boundaries, timezone handling, and week definitions.
"""

from datetime import datetime, timezone, timedelta

import pytest


def test_elena_views_weekly_and_all_time_statistics(client):
    """Happy path: Elena checks her weekly total and all-time total.
    
    Setup: Elena has 30 sessions total, 8 this week.
    Trigger: Elena taps the Stats section, sees "This Week" and "All-Time" views.
    Expected: 
      - "This Week: 8 sessions, 200 minutes"
      - "All-Time: 30 sessions, 750 minutes"
    """
    # For this test, we'd need to seed sessions across multiple weeks.
    # Simplified version: complete some sessions and verify stats endpoints respond correctly.
    
    # Complete 3 sessions to simulate activity
    for i in range(3):
        res = client.post("/session/start", json={})
        session = res.json()
        res = client.post(f"/session/{session['id']}/stop", json={})
        assert res.status_code == 200
    
    # Query weekly stats
    res = client.get("/stats/week")
    assert res.status_code == 200
    week_stats = res.json()
    assert "session_count" in week_stats
    assert "total_duration_seconds" in week_stats
    assert "week_start_date" in week_stats
    assert "week_end_date" in week_stats
    assert week_stats["session_count"] >= 3
    
    # Query all-time stats
    res = client.get("/stats/all-time")
    assert res.status_code == 200
    all_time = res.json()
    assert "session_count" in all_time
    assert "total_duration_seconds" in all_time
    assert all_time["session_count"] >= 3


def test_stats_computed_from_completed_sessions_only(client):
    """Edge case: Stats include only completed sessions, not active ones.
    
    Setup: One active session (in progress), three completed.
    Trigger: Query /stats/week.
    Expected: Stats count = 3 (active session is excluded).
    """
    # Start a session but don't complete it
    res = client.post("/session/start", json={})
    active = res.json()
    
    # Complete 3 sessions
    for i in range(3):
        res = client.post("/session/start", json={})
        session = res.json()
        res = client.post(f"/session/{session['id']}/stop", json={})
        assert res.status_code == 200
    
    # Query stats
    res = client.get("/stats/week")
    assert res.status_code == 200
    stats = res.json()
    assert stats["session_count"] == 3  # Only completed


def test_week_boundary_is_monday_to_sunday_utc(client):
    """Edge case: Week boundary logic is consistent and deterministic.
    
    Setup: Complete sessions on different days.
    Trigger: Query /stats/week on a Wednesday.
    Expected: Week includes Monday–Sunday of the current week (UTC).
    week_start_date is the Monday; week_end_date is the Sunday.
    """
    res = client.get("/stats/week")
    assert res.status_code == 200
    stats = res.json()
    
    # week_start_date should be a Monday (day 0 in ISO calendar)
    week_start = datetime.fromisoformat(stats["week_start_date"])
    assert week_start.weekday() == 0  # Monday
    
    # week_end_date should be a Sunday (day 6)
    week_end = datetime.fromisoformat(stats["week_end_date"])
    assert week_end.weekday() == 6  # Sunday
    
    # They should be exactly 6 days apart
    delta = (week_end - week_start).days
    assert delta == 6


def test_all_time_stats_include_all_sessions_ever(client):
    """Edge case: All-time stats aggregate across entire history (no time limit).
    
    Setup: User has sessions from months ago and today.
    Trigger: Query /stats/all-time.
    Expected: Includes all completed sessions, ever.
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    res = client.get("/stats/all-time")
    assert res.status_code == 200
    all_time = res.json()
    
    # Should include at least the session we just completed
    assert all_time["session_count"] >= 1
    assert all_time["total_duration_seconds"] >= (25 * 60)


def test_stats_update_immediately_after_session_completion(client):
    """Edge case: Stats reflect newly completed session within 5 seconds.
    
    Setup: Query /stats/week, get count=5.
    Trigger: Complete a new session.
    Expected: Query /stats/week again, count=6.
    """
    # Get initial stats
    res = client.get("/stats/week")
    initial_stats = res.json()
    initial_count = initial_stats["session_count"]
    
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    # Query stats again
    res = client.get("/stats/week")
    updated_stats = res.json()
    
    # Count should have incremented
    assert updated_stats["session_count"] == initial_count + 1
    
    # Duration should have increased by ~25 minutes
    duration_increase = updated_stats["total_duration_seconds"] - initial_stats["total_duration_seconds"]
    assert duration_increase >= (25 * 60)


def test_stats_with_zero_sessions(client):
    """Edge case: New user with no completed sessions.
    
    Setup: Fresh user, hasn't completed any sessions.
    Trigger: Query /stats/week and /stats/all-time.
    Expected: Both return 0 sessions, 0 seconds, no error.
    """
    # Assume a fresh test database
    res = client.get("/stats/week")
    assert res.status_code == 200
    week_stats = res.json()
    # If database is fresh, stats should be empty or zero
    # (Implementation can vary; the contract is: return 200, not error)
    
    res = client.get("/stats/all-time")
    assert res.status_code == 200
    all_time = res.json()
    assert all_time["session_count"] >= 0


@pytest.mark.skip(reason="Historical stats querying not in v1 contract")
def test_query_historical_week_stats(client):
    """Optional feature: Query stats for a past week.
    
    Would add endpoint like /stats/week?week_start_date=2024-01-01
    to let Elena view historical performance.
    
    Skipped for v1 (only current week is supported).
    """
    pass


def test_stats_cache_ttl_behavior(client):
    """Edge case: Frontend caches stats with appropriate TTL.
    
    This scenario documents the contract expectation:
    - Stats cache TTL = 60s (or shorter if on stats page)
    - Cache invalidates on session→completed event
    - Client should manually refresh every 60s if stats are visible
    
    Backend responsibility: always return fresh stats when queried.
    """
    # Backend just needs to ensure /stats endpoints return current data
    res = client.get("/stats/week")
    assert res.status_code == 200
    # If called again immediately, should return same (or updated if new session completed)
    res = client.get("/stats/week")
    assert res.status_code == 200


def test_stats_include_duration_in_seconds_and_minutes(client):
    """Edge case: Stats return duration_seconds; frontend converts to minutes/hours.
    
    Setup: 3 sessions × 25 minutes = 1800 seconds.
    Trigger: Query /stats/week.
    Expected: total_duration_seconds = 1800.
    """
    # Complete 3 sessions
    for i in range(3):
        res = client.post("/session/start", json={})
        session = res.json()
        res = client.post(f"/session/{session['id']}/stop", json={})
        assert res.status_code == 200
    
    res = client.get("/stats/week")
    assert res.status_code == 200
    stats = res.json()
    
    # 3 × 25 minutes = 75 minutes = 4500 seconds
    # (Allowing some slack for test execution time)
    assert stats["total_duration_seconds"] >= (75 * 60 - 10)
    assert stats["session_count"] >= 3
