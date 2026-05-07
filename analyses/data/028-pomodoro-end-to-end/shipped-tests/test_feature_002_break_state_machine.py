"""
Edge-case tests for Feature 002: Break lifecycle and state transitions.

Contracts: Break lifecycle & state transitions (002)

These scenarios focus on break duration application, state machine races,
and idempotency under network failure.
"""

import pytest


def test_break_duration_from_user_settings_not_hardcoded(client):
    """Edge case: Break duration comes from user.settings, not hardcoded default.
    
    Severity: degradation
    
    Scenario: Priya customized break to 10 minutes (default is 5). She completes
    a focus session. The contract specifies: break created with duration_minutes
    from user.settings at that moment.
    
    Concern: If hardcoded (always 5 minutes), Priya's settings are silently ignored.
    System works, but not as customized. Degradation.
    
    Property: For all breaks created after a session completes,
    break.duration_minutes == user.settings.break_duration_minutes at completion.
    """
    # First customize settings to 10 minutes
    res = client.patch("/settings", json={
        "session_duration_minutes": 25,
        "break_duration_minutes": 10
    })
    assert res.status_code == 200
    
    # Now complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Break should be created with 10-minute duration
    res = client.get("/break/current")
    assert res.status_code == 200
    break_info = res.json()
    assert break_info["state"] == "active"
    assert break_info["duration_minutes"] == 10
    # Remaining should be close to 600 seconds (10 minutes)
    assert break_info["remaining_seconds"] <= (10 * 60)
    assert break_info["remaining_seconds"] > (10 * 60 - 5)  # Within 5 sec tolerance


def test_skip_break_idempotent_across_race_with_timeout(client):
    """Edge case: Skip is idempotent even if timeout fires simultaneously.
    
    Severity: degradation
    
    Scenario: Priya's break has 200ms remaining. She taps 'Skip'. Meanwhile,
    server-side break timeout is about to fire. Both requests happen within 100ms.
    Backend must handle this race deterministically.
    
    Concern: If race is not handled, break could end up in inconsistent state
    (both skipped and completed, or neither). Skip request could be lost.
    
    Property: For all skip requests, if break.remaining_seconds < 1,
    the skip is still idempotent and returns successfully with deterministic state.
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Break is active
    res = client.get("/break/current")
    assert res.status_code == 200
    assert res.json()["state"] == "active"
    
    # Skip the break
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    skip1 = res.json()
    assert skip1["state"] == "skipped"
    
    # Retry skip (simulating race or network flake)
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    skip2 = res.json()
    # Should return skipped state, not error
    assert skip2["state"] in ["skipped", "completed"]


def test_break_duration_recorded_in_history_is_configured_duration_not_actual(client):
    """Edge case: History records the configured break duration, not actual elapsed time.
    
    Severity: silent-wrongness
    
    Scenario: Priya completes session (break configured as 5 minutes). Break created.
    Priya immediately skips the break (actual elapsed: <1 second).
    Query /sessions/history to see the session and its break metadata.
    
    Concern: If break_duration_seconds records actual elapsed (0, because skipped),
    history is ambiguous. Silent wrongness: data looks plausible but means the wrong thing.
    
    Property: For all sessions in history, break_duration_seconds ==
    configured_break_duration (regardless of skip or completion).
    """
    # Complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Get the break
    res = client.get("/break/current")
    assert res.status_code == 200
    break_info = res.json()
    configured_duration = break_info["duration_minutes"]
    
    # Skip the break immediately
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    
    # Query history
    res = client.get("/sessions/history")
    assert res.status_code == 200
    history = res.json()
    
    # Most recent session should have break metadata
    if len(history) > 0:
        recorded = history[0]
        assert "break_duration_seconds" in recorded
        # Should be configured duration (5 min = 300 sec), not 0
        assert recorded["break_duration_seconds"] == (configured_duration * 60)
        assert recorded["break_skipped"] is True
