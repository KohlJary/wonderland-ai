"""User journey scenarios for focus session feature.

These test that the focus session feature works for Marcus: he can start
a timer, watch it count down, and get a signal when it ends. He can also
pause and resume without losing his place.

The scenarios in this file are *aspirational* — they describe what the
feature should do, not what the backend currently does. They are written
as pytest fixtures + test functions to make the surface concrete, even
though the implementation is still ahead.

The TestClient here exercises the backend API layer, which is the boundary
where Alice's user journey meets the code. Frontend-specific behavior
(animation, sound playback, etc.) is not tested here; those belong in
frontend tests.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone


@pytest.mark.skip(reason="backend models not yet implemented")
def test_marcus_starts_focus_session_and_watches_countdown(client: TestClient):
    """
    **Scenario:** Marcus starts a 25-minute focus session
    
    Marcus opens the app, taps 'Start Focus', and the timer begins counting down.
    He watches the UI show remaining time, updates every second.
    
    **Observable:** 
    - Session is created with status='running'
    - Time remaining decreases by 1 second per second
    - After 25 minutes, the session completes
    
    **Test shape:**
    - POST /sessions/focus to start
    - Poll GET /sessions/current to observe time remaining
    - Verify status transitions from 'running' to 'completed'
    """
    # POST /sessions/focus starts a session
    response = client.post("/sessions/focus", json={})
    assert response.status_code == 201
    session_data = response.json()
    assert session_data["status"] == "running"
    assert session_data["duration"] == 1500  # 25 minutes in seconds
    assert "started_at" in session_data
    
    session_id = session_data["id"]
    
    # GET /sessions/current returns the running session
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    current = response.json()
    assert current["status"] == "running"
    # Elapsed time is small (just started)
    assert current["elapsed_seconds"] < 5


@pytest.mark.skip(reason="backend models not yet implemented")
def test_marcus_pauses_session_mid_countdown_and_resumes(client: TestClient):
    """
    **Scenario:** Marcus pauses at 15 minutes remaining and resumes
    
    Marcus is 10 minutes into the session. He gets distracted and pauses.
    The countdown stops. He returns and resumes. The countdown picks up
    where he left off: 15 minutes remaining still.
    
    **Observable:**
    - Session status becomes 'paused'
    - Time remaining freezes at the pause point
    - Resume transitions status back to 'running'
    - Timer continues from the pause point (no time lost)
    
    **Test shape:**
    - POST /sessions/focus
    - PATCH /sessions/{id} { "action": "pause" }
    - Verify status='paused', elapsed_seconds frozen
    - PATCH /sessions/{id} { "action": "resume" }
    - Verify status='running', elapsed_seconds unchanged
    """
    # Start a session
    response = client.post("/sessions/focus", json={})
    session_id = response.json()["id"]
    
    # Pause the session
    response = client.patch(f"/sessions/{session_id}", json={"action": "pause"})
    assert response.status_code == 200
    paused_data = response.json()
    assert paused_data["status"] == "paused"
    elapsed_at_pause = paused_data["elapsed_seconds"]
    
    # Resume the session
    response = client.patch(f"/sessions/{session_id}", json={"action": "resume"})
    assert response.status_code == 200
    resumed_data = response.json()
    assert resumed_data["status"] == "running"
    # Elapsed time should not have advanced during pause
    assert resumed_data["elapsed_seconds"] <= elapsed_at_pause + 2  # +2 for any clock drift
