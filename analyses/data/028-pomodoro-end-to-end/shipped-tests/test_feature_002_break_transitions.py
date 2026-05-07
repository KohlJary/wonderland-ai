"""
Test scenarios for Feature 002: Take a structured break and transition to the next session.

Contracts: Break lifecycle & state transitions (002)
Persona: Priya, designer who needs the system to push her toward actual rest

Tests the happy path (session ends, break auto-starts, user can skip or wait)
and edge cases around break state transitions, idempotency, and race conditions.
"""

import pytest


def test_priya_completes_session_break_auto_starts(client):
    """Happy path: Priya's session ends; break timer automatically begins.
    
    Setup: Priya is mid-session (25 minutes, 5 remaining).
    Trigger: Session completes (either timeout or manual stop).
    Expected: Break state becomes active, /break/current returns break with 5:00 countdown.
    """
    # Start a session
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session = res.json()
    session_id = session["id"]
    
    # Complete the session
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    stopped_session = res.json()
    assert stopped_session["state"] == "completed"
    
    # Check that break is now active
    res = client.get("/break/current")
    assert res.status_code == 200
    break_info = res.json()
    assert break_info["state"] == "active"
    assert break_info["remaining_seconds"] <= (5 * 60)
    assert break_info["remaining_seconds"] > 0
    assert break_info["skip_available"] is True


def test_priya_can_skip_break_and_start_next_session(client):
    """Edge case: Priya decides she's ready to go; she skips the break.
    
    Setup: Break is active, showing 5:00 remaining, "Skip" button available.
    Trigger: Priya taps 'Skip Break'.
    Expected: Break transitions to skipped, /break/current returns skipped state.
    Next session can be started immediately.
    """
    # Start and complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Break is now active
    res = client.get("/break/current")
    assert res.status_code == 200
    assert res.json()["state"] == "active"
    
    # Skip the break
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    skipped = res.json()
    assert skipped["state"] == "skipped"
    
    # Now user can start the next session
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    next_session = res.json()
    assert next_session["state"] == "active"
    assert next_session["id"] != session_id


def test_skip_break_is_idempotent(client):
    """Edge case: User taps skip twice (network flake); skip is idempotent.
    
    Setup: Break is active.
    Trigger: User taps Skip, gets no response, taps Skip again.
    Expected: First skip transitions break→skipped. Second skip returns the same skipped state.
    """
    # Start, complete, break starts
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # First skip
    res1 = client.post("/break/skip", json={})
    assert res1.status_code == 200
    skip1 = res1.json()
    assert skip1["state"] == "skipped"
    
    # Second skip (retry)
    res2 = client.post("/break/skip", json={})
    assert res2.status_code == 200
    skip2 = res2.json()
    assert skip2["state"] == "skipped"
    # Should be the same break, not a new one


def test_break_duration_uses_user_settings(client):
    """Edge case: Break duration comes from user's Settings, not hardcoded.
    
    Setup: User has customized settings to 10-minute breaks (default is 5).
    Trigger: User completes a session.
    Expected: Break starts with 10:00 duration, not 5:00.
    
    This pins the invariant: user preferences affect break behavior.
    """
    # First, customize settings (Feature 005)
    res = client.patch("/settings", json={
        "session_duration_minutes": 25,
        "break_duration_minutes": 10
    })
    assert res.status_code == 200
    
    # Now start and complete a session
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Break should reflect the 10-minute setting
    res = client.get("/break/current")
    assert res.status_code == 200
    break_info = res.json()
    assert break_info["duration_minutes"] == 10
    assert break_info["remaining_seconds"] <= (10 * 60)


@pytest.mark.skip(reason="Break timeout not yet fully specified; testing implicit contract")
def test_break_timeout_fires_and_transitions_to_completed(client):
    """Edge case: If user doesn't skip and waits, break times out after duration.
    
    Setup: Break is active, 5:00 duration.
    Trigger: 5 minutes elapse.
    Expected: Break state transitions to completed, /break/current returns completed state.
    Client can then start a new session.
    
    This test is skipped pending clarification on server-side timeout mechanism.
    """
    pass


@pytest.mark.skip(reason="Race condition testing requires time-warping mocks")
def test_race_skip_and_timeout_both_in_flight(client):
    """Edge case: Skip request in-flight while break timeout fires simultaneously.
    
    Setup: Break is active, 100ms remaining. User taps Skip.
    Trigger: /break/skip request sent, but 100ms elapses before reaching server.
    Meanwhile, break timeout fires server-side.
    Expected: Last-write-wins or explicit conflict handling; break ends up in
    one final state (skipped or completed), not both.
    
    Requires time-warping mocks; skipped for now.
    """
    pass


def test_break_info_persists_in_session_history(client):
    """Edge case: Break state is recorded in session history for later review.
    
    Setup: User completes session, takes break (skips, or waits out).
    Trigger: Query /sessions/history to get details of the completed session.
    Expected: History includes break_duration_seconds and break_skipped boolean,
    so user can see which sessions had a break and which were skipped.
    """
    # Complete a session with break
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    
    # Skip the break
    res = client.post("/break/skip", json={})
    assert res.status_code == 200
    
    # Query history
    res = client.get("/sessions/history")
    assert res.status_code == 200
    history = res.json()
    
    # The completed session should appear with break info
    assert len(history) > 0
    recorded = history[0]
    assert recorded["break_skipped"] is True
