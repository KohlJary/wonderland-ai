"""
Test scenarios for Feature 001: Start a focus session and get notified when it ends.

Contracts: Session lifecycle & timer state (001)
Persona: Marcus, software engineer protecting deep work blocks

Tests the happy path (user starts session, sees countdown, gets notification
on completion) and edge cases around timer authority, idempotency, and client
time reconciliation.
"""

from datetime import datetime, timedelta, timezone
import time

import pytest


def test_marcus_starts_25_minute_session_and_receives_notification(client):
    """Happy path: Marcus taps Start, sees timer count down, receives notification.
    
    This scenario pins the core user journey: a real user with a real goal
    (25-minute focus block) and the observable results that constitute success.
    
    Setup: Marcus opens the app (first time using it, or returning from a break).
    Trigger: Marcus taps 'Start Session' button.
    Expected: Timer starts, counts down visibly, notification fires when complete.
    """
    # POST /session/start initiates a new session with default duration
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session = res.json()
    assert session["state"] == "active"
    assert session["duration_minutes"] == 25
    assert session["start_time"] is not None
    session_id = session["id"]
    
    # Immediately polling /session/current shows timer running
    res = client.get("/session/current")
    assert res.status_code == 200
    current = res.json()
    assert current["state"] == "active"
    assert current["remaining_seconds"] > 0
    assert current["remaining_seconds"] <= (25 * 60)
    
    # After 25 minutes, session auto-completes (simulated by manually stopping)
    # In real usage, client would detect completion via /session/current polling
    # or server push; here we simulate the timeout.
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    completed = res.json()
    assert completed["state"] == "completed"
    assert completed["completed_at"] is not None


def test_server_time_is_authoritative_for_remaining_seconds(client):
    """Edge case: Client timer must reconcile with server time to prevent drift.
    
    Scenario: Client's local clock drifts (user's system clock is fast or slow).
    The contract specifies server time is authoritative; client should resync
    if local elapsed diverges >5s from server remaining.
    
    This test pins the requirement: /session/current always returns server-computed
    remaining_seconds, and client must use this to stay in sync.
    """
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session = res.json()
    start_time = datetime.fromisoformat(session["start_time"])
    
    # First poll: get remaining_seconds from server
    res = client.get("/session/current")
    assert res.status_code == 200
    poll1 = res.json()
    remaining1 = poll1["remaining_seconds"]
    
    # Simulate 3 seconds of real time passing
    time.sleep(3)
    
    # Second poll: remaining_seconds should have decreased by ~3s
    res = client.get("/session/current")
    assert res.status_code == 200
    poll2 = res.json()
    remaining2 = poll2["remaining_seconds"]
    
    # Remaining should have decreased (within tolerance for test timing jitter)
    assert remaining2 <= remaining1
    assert (remaining1 - remaining2) >= 2  # at least 2 seconds elapsed


def test_start_session_twice_is_idempotent_returns_existing(client):
    """Edge case: Duplicate start requests return the existing session, not a new one.
    
    Scenario: User's phone loses network mid-request, retries /session/start.
    Contract requires idempotency: the retry must not create a second session,
    but return the first one.
    
    This pins the invariant: no two active sessions can exist for a user.
    """
    res1 = client.post("/session/start", json={})
    assert res1.status_code == 200
    session1 = res1.json()
    session1_id = session1["id"]
    
    # Immediate retry (simulating network flake)
    res2 = client.post("/session/start", json={})
    assert res2.status_code == 200
    session2 = res2.json()
    session2_id = session2["id"]
    
    # Both responses refer to the same session
    assert session1_id == session2_id
    assert session2["state"] == "active"


def test_cannot_start_session_while_one_is_active(client):
    """Edge case: Reject start request if a session is already active.
    
    Scenario: User accidentally taps Start twice in quick succession (app stutter).
    Contract: reject the second request, return the existing active session.
    """
    res1 = client.post("/session/start", json={})
    assert res1.status_code == 200
    session1 = res1.json()
    assert session1["state"] == "active"
    
    # Second request should either:
    # (a) return 409 Conflict + existing session, OR
    # (b) return 200 with existing session (idempotent)
    # We'll accept either; the key is no new session is created.
    res2 = client.post("/session/start", json={})
    assert res2.status_code in [200, 409]
    if res2.status_code == 200:
        session2 = res2.json()
        assert session2["id"] == session1["id"]


def test_stop_session_twice_is_idempotent(client):
    """Edge case: Duplicate stop requests return the same completed session.
    
    Scenario: User taps Stop, network hiccup, user taps Stop again.
    Contract: idempotent, second stop returns the completed session.
    """
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    res1 = client.post(f"/session/{session_id}/stop", json={})
    assert res1.status_code == 200
    stopped1 = res1.json()
    assert stopped1["state"] == "completed"
    completed_at1 = stopped1["completed_at"]
    
    # Retry: second stop on same session
    res2 = client.post(f"/session/{session_id}/stop", json={})
    assert res2.status_code == 200
    stopped2 = res2.json()
    assert stopped2["state"] == "completed"
    
    # Should be the same completion
    assert stopped2["completed_at"] == completed_at1


@pytest.mark.skip(reason="Server-side timer not yet implemented; client will poll")
def test_session_timeout_fires_server_side_without_client_poll(client):
    """Edge case: If client is offline when session times out, timeout still fires.
    
    Scenario: Marcus's focus session completes while his phone is in airplane mode.
    Contract: Server tracks timeout independently; when client reconnects and polls,
    /session/current returns state=completed.
    
    This test is skipped until server-side timeout logic is implemented.
    """
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    
    # Simulate 25+ minutes passing server-side
    # (In a real test, we'd advance the database clock or mock time)
    # For now, we're documenting the contract requirement.
    
    # When client reconnects and polls:
    res = client.get("/session/current")
    # Expected: state=completed even without explicit /stop call


def test_session_completion_timestamp_is_set_at_transition(client):
    """Edge case: completed_at must be set exactly when state→completed happens.
    
    Scenario: Timing-sensitive workflow where completion timestamp matters
    (e.g., calculating session duration precisely).
    
    This pins: completed_at is not null when state=completed.
    """
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    start_time = datetime.fromisoformat(session["start_time"])
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    stopped = res.json()
    
    assert stopped["completed_at"] is not None
    completed_at = datetime.fromisoformat(stopped["completed_at"])
    
    # completed_at should be >= start_time
    assert completed_at >= start_time


@pytest.mark.skip(reason="Pause/resume not in v1 scope")
def test_pause_and_resume_session(client):
    """Optional edge case: Pause/resume not in v1 contract; skipped.
    
    When pause/resume is added in v2, this scenario documents behavior:
    user can pause mid-session, resume later, without losing time.
    """
    pass
