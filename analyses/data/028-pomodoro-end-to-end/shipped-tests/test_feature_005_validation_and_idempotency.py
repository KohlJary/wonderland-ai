"""
Edge-case tests for Feature 005: Settings validation and idempotency.

Contracts: User preferences & duration customization (005)

These scenarios focus on validation bounds, partial updates, active-session
invariants, and idempotency.
"""

import pytest


def test_settings_validation_rejects_out_of_bounds_values(client):
    """Edge case: Settings validation enforces [1, 180] minute bounds.
    
    Severity: degradation
    
    Scenario: Dev tries to set duration to 0 (invalid), 1 (valid), 180 (valid), 181 (invalid).
    PATCH /settings with each value.
    
    Concern: If validation is loose, Dev could set 0-second session or 24-hour session,
    breaking UI assumptions and timer logic.
    
    Property: For all PATCH /settings requests, if session_duration_minutes or
    break_duration_minutes is not in [1, 180], the server returns HTTP 400 or 422
    and does not update settings.
    """
    # Try to set to 0 (invalid)
    res = client.patch("/settings", json={
        "session_duration_minutes": 0,
        "break_duration_minutes": 5
    })
    assert res.status_code in [400, 422]
    
    # Try to set to 1 (valid edge)
    res = client.patch("/settings", json={
        "session_duration_minutes": 1,
        "break_duration_minutes": 1
    })
    assert res.status_code == 200
    settings = res.json()
    assert settings["session_duration_minutes"] == 1
    
    # Try to set to 180 (valid edge)
    res = client.patch("/settings", json={
        "session_duration_minutes": 180,
        "break_duration_minutes": 180
    })
    assert res.status_code == 200
    settings = res.json()
    assert settings["session_duration_minutes"] == 180
    
    # Try to set to 181 (invalid)
    res = client.patch("/settings", json={
        "session_duration_minutes": 181,
        "break_duration_minutes": 5
    })
    assert res.status_code in [400, 422]


def test_partial_settings_update_doesnt_touch_omitted_field(client):
    """Edge case: Patching one field doesn't reset the other to default.
    
    Severity: degradation
    
    Scenario: Dev's current settings are {session: 25, break: 5}. Dev sends
    PATCH /settings with {session_duration_minutes: 45} (break omitted).
    
    Concern: If omitted field resets to default, Dev loses customization.
    
    Property: For all PATCH /settings requests, if a field is omitted,
    the server does not modify that field from its current value.
    """
    # First set both values
    res = client.patch("/settings", json={
        "session_duration_minutes": 30,
        "break_duration_minutes": 7
    })
    assert res.status_code == 200
    
    # Now patch only session duration (omit break)
    res = client.patch("/settings", json={
        "session_duration_minutes": 45
    })
    assert res.status_code == 200
    updated = res.json()
    
    # Session should be updated, break should remain
    assert updated["session_duration_minutes"] == 45
    assert updated["break_duration_minutes"] == 7


def test_active_session_duration_not_retroactively_changed(client):
    """Edge case: Changing settings mid-session doesn't affect the active session.
    
    Severity: degradation
    
    Scenario: Dev starts a 25-minute session (default). 5 minutes in, Dev opens
    Settings and changes to 50 minutes.
    
    Concern: If settings changes apply retroactively, timer would jump,
    breaking the timer contract and user trust.
    
    Property: For all active sessions, if PATCH /settings is called,
    the active session.duration_minutes does not change.
    Settings apply only to new sessions.
    """
    # Start a session with default duration
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session1 = res.json()
    assert session1["duration_minutes"] == 25
    session1_id = session1["id"]
    
    # Change settings while session is active
    res = client.patch("/settings", json={
        "session_duration_minutes": 50,
        "break_duration_minutes": 10
    })
    assert res.status_code == 200
    
    # Active session still has original duration
    res = client.get("/session/current")
    assert res.status_code == 200
    current = res.json()
    assert current["duration_minutes"] == 25
    
    # Stop the session
    res = client.post(f"/session/{session1_id}/stop", json={})
    assert res.status_code == 200
    stopped = res.json()
    assert stopped["duration_minutes"] == 25
    
    # Next session uses new duration
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session2 = res.json()
    assert session2["duration_minutes"] == 50


def test_settings_patch_is_idempotent(client):
    """Edge case: Sending the same PATCH twice is safe (no side effects).
    
    Severity: degradation
    
    Scenario: Dev taps Save on settings form. Request sent, client unsure if reached
    server, retries. Both requests should return identical results.
    
    Property: For all PATCH /settings requests with identical values sent twice,
    both requests return 200 with the same result.
    """
    # First PATCH
    res1 = client.patch("/settings", json={
        "session_duration_minutes": 50,
        "break_duration_minutes": 10
    })
    assert res1.status_code == 200
    result1 = res1.json()
    
    # Second PATCH (retry) with same values
    res2 = client.patch("/settings", json={
        "session_duration_minutes": 50,
        "break_duration_minutes": 10
    })
    assert res2.status_code == 200
    result2 = res2.json()
    
    # Both should return identical results
    assert result1 == result2
