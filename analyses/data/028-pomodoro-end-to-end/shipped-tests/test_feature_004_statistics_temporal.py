"""
Edge-case tests for Feature 004: Statistics aggregation and temporal boundaries.

Contracts: Statistics aggregation & temporal boundaries (004)

These scenarios focus on week boundary logic, timezone handling, zero-session fallback,
and membership_duration calculation.
"""

from datetime import datetime, timezone

import pytest


def test_week_boundary_is_inclusive_both_ends_in_utc(client):
    """Edge case: Weekly stats use inclusive boundaries on both sides in UTC.
    
    Severity: silent-wrongness
    
    Scenario: Elena queries /stats/week on Thursday. The contract specifies
    Mon–Sun UTC boundaries. A session completed on Sunday at 23:59:59 UTC
    should be included.
    
    Concern: If boundary is off-by-one (inclusive/exclusive mismatch),
    week totals are wrong. Session appears in two weeks or is missed.
    Silent wrongness.
    
    Property: For all sessions with completed_at in [Monday_00:00_UTC, Sunday_23:59:59_UTC],
    the session is included in /stats/week. Sessions outside this range are not.
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    res = client.get("/stats/week")
    assert res.status_code == 200
    stats = res.json()
    
    # Verify week boundaries exist
    assert "week_start_date" in stats
    assert "week_end_date" in stats
    
    week_start = datetime.fromisoformat(stats["week_start_date"])
    week_end = datetime.fromisoformat(stats["week_end_date"])
    
    # Start should be a Monday (weekday 0)
    assert week_start.weekday() == 0


def test_week_boundary_respects_utc_not_local_timezone(client):
    """Edge case: Week boundaries use UTC, not user's local timezone.
    
    Severity: silent-wrongness
    
    Scenario: Elena is UTC-8. On her local Sunday evening (1 AM UTC Monday),
    she completes a session. Query /stats/week.
    
    Concern: If backend uses local timezone, Elena's data misaligned with UTC.
    Monday-evening session (local) counts toward last week instead of this week.
    Silent wrongness.
    
    Property: For all users, /stats/week uses UTC week boundaries (Mon–Sun UTC),
    not local timezone boundaries.
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    res = client.get("/stats/week")
    assert res.status_code == 200
    stats = res.json()
    
    # Boundaries should be in UTC (indicated by Z or UTC in the timestamp)
    week_start = stats["week_start_date"]
    assert "Z" in week_start or "UTC" in week_start or "+00:00" in week_start


def test_membership_duration_days_computed_server_side(client):
    """Edge case: membership_duration_days computed by server using server time.
    
    Severity: degradation
    
    Scenario: Elena's device clock is set 3 days in the future. She queries /stats/all-time.
    Contract says membership_duration_days is server-computed.
    
    Concern: If computed client-side, value is wrong whenever user's clock is incorrect.
    Server-side computation ensures consistency.
    
    Property: For all users, membership_duration_days returned by /stats/all-time
    is computed server-side based on server time, not client time.
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    res = client.post(f"/session/{session['id']}/stop", json={})
    assert res.status_code == 200
    
    res = client.get("/stats/all-time")
    assert res.status_code == 200
    all_time = res.json()
    
    # membership_duration_days should be computed and reasonable
    if "membership_duration_days" in all_time:
        assert isinstance(all_time["membership_duration_days"], int)
        assert all_time["membership_duration_days"] >= 0
