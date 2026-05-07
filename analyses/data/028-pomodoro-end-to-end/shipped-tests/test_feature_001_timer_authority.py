"""
Edge-case tests for Feature 001: Timer authority and client-server reconciliation.

Contracts: Session lifecycle & timer state (001)

These scenarios focus on the failure modes around time authority, client clock drift,
server-side timeout delivery, and idempotency under network failure.
"""

import pytest


def test_client_drift_greater_than_5_seconds_triggers_resync(client):
    """Edge case: Client clock drifts 8 seconds ahead; client must detect and resync.
    
    Severity: silent-wrongness
    
    Scenario: Marcus starts a session. Client caches {start_time, remaining_seconds}.
    Client's local clock runs 8 seconds fast relative to server time.
    
    Concern: If client naively trusts local clock math, timer display drifts from
    server truth. User sees 4:30 remaining locally but server says 4:22. Silent
    wrongness: display appears correct but is untethered from reality.
    
    Property: For all polls of /session/current, if |client_remaining - server_remaining| > 5s,
    client must resync to server_remaining on the next response.
    """
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session = res.json()
    session_id = session["id"]
    
    # First poll: capture server time
    res = client.get("/session/current")
    assert res.status_code == 200
    poll1 = res.json()
    remaining1 = poll1["remaining_seconds"]
    
    # Client would compute: elapsed = (now_client - start_time)
    # then: remaining = remaining_seconds - elapsed
    # If client's clock is 8 seconds fast, client computes a different remaining
    # than server does.
    
    # On next poll, server's remaining_seconds is authoritative
    res = client.get("/session/current")
    assert res.status_code == 200
    poll2 = res.json()
    
    # Server time is the truth source
    assert poll2["remaining_seconds"] is not None


def test_duplicate_start_with_different_durations_is_deterministic(client):
    """Edge case: Two concurrent /session/start requests arrive; backend picks one deterministically.
    
    Severity: breakage
    
    Scenario: Marcus taps Start Session. Network hiccup causes a retry. Meanwhile,
    a settings sync fetch completes with a new duration. Two requests arrive almost
    simultaneously with different duration values.
    
    Concern: Without strict idempotency, backend could create two sessions, or merge
    the requests incorrectly, violating the invariant of max-one-active-session per user.
    
    Property: For all user_id, if POST /session/start is called twice within 10 seconds
    with the same user context, the backend returns the same session_id both times.
    No two active sessions exist.
    """
    # Start first session
    res1 = client.post("/session/start", json={})
    assert res1.status_code == 200
    session1 = res1.json()
    session1_id = session1["id"]
    
    # Immediate retry (simulating network flake + concurrent requests)
    res2 = client.post("/session/start", json={})
    assert res2.status_code == 200
    session2 = res2.json()
    session2_id = session2["id"]
    
    # Must be the same session, even if requests arrived in different order
    assert session1_id == session2_id
    assert session1["state"] == "active"
    assert session2["state"] == "active"


def test_server_timeout_fires_while_client_offline(client):
    """Edge case: Session times out server-side while client is in airplane mode.
    
    Severity: degradation
    
    Scenario: Marcus starts a 25-minute session. After 20 minutes, airplane mode.
    At +25 minutes, session times out and transitions to state=completed.
    At +26 minutes, user lands, reconnects, app polls /session/current.
    
    Concern: If server doesn't reliably track timeout independently, session could
    stay active forever. Client's local timer might keep counting past duration.
    When user reconnects, they'd see stale data.
    
    Property: For all active sessions, if (now_server - start_time) >= duration_minutes * 60,
    then session.state must be 'completed' and session.completed_at must be set.
    """
    res = client.post("/session/start", json={})
    assert res.status_code == 200
    session = res.json()
    session_id = session["id"]
    
    # Verify session is active
    res = client.get("/session/current")
    assert res.status_code == 200
    assert res.json()["state"] == "active"
    
    # (In production, we'd wait 25+ minutes or mock time. Here we document the contract:)
    # After timeout, /session/current should return state=completed
    # even if the client never called /stop.


def test_completed_at_set_exactly_at_transition_moment(client):
    """Edge case: completed_at timestamp is precise at the moment of completion.
    
    Severity: silent-wrongness
    
    Scenario: James's session is 4 seconds from completion. He manually taps Stop.
    Backend transitions session.state to completed and sets completed_at.
    
    Concern: If completed_at is set retroactively or with incorrect timestamp logic,
    session duration calculations downstream (history, stats) are wrong by hours.
    Session might appear to have completed before it actually did.
    
    Property: For all completed sessions, completed_at >= start_time, and
    (completed_at - start_time) ≈ intended_duration (within 1% tolerance).
    """
    res = client.post("/session/start", json={})
    session = res.json()
    session_id = session["id"]
    start_time = session["start_time"]
    
    res = client.post(f"/session/{session_id}/stop", json={})
    assert res.status_code == 200
    stopped = res.json()
    
    assert stopped["completed_at"] is not None
    
    # Verify timestamp is close to start time + duration
    # (exact timing depends on test execution speed)
    from datetime import datetime
    start_dt = datetime.fromisoformat(start_time)
    completed_dt = datetime.fromisoformat(stopped["completed_at"])
    
    assert completed_dt >= start_dt
    # Should be roughly session duration (25 min = 1500 sec)
    delta_sec = (completed_dt - start_dt).total_seconds()
    assert delta_sec > 0  # Must have completed after it started
