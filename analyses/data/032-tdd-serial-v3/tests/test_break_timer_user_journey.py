"""User journey scenarios for break timer with user configuration feature.

These test that Keisha (a project manager managing fatigue) can:
1. Set a default break duration in settings (persistent across launches)
2. Have the break timer start automatically when her focus session ends
3. Adjust the break duration mid-focus without losing her default
4. Skip a break and go straight to the next focus session

The scenarios in this file describe what the feature should do from Keisha's
standpoint. They are written as pytest fixtures + test functions to make the
surface concrete, even though backend models are still ahead.

The TestClient here exercises the backend API layer. Frontend-specific behavior
(localStorage reads, UI transitions, audio playback) is tested in frontend tests.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_sets_break_duration_and_it_starts_automatically_on_focus_end(
    client: TestClient,
):
    """
    **Scenario:** Keisha sets break duration to 600s and focus transitions to break

    Keisha opens settings and changes the default break duration from 300 to
    600 seconds. She then starts a focus session. When the focus session ends
    (or is manually ended for testing), the break timer should start
    automatically with 600 seconds remaining.

    **Observable:**
    - Settings POST updates break_duration_seconds to 600
    - Focus session is created and running
    - Break session starts automatically when focus completes, with 600s remaining
    - Break session status is 'running', type is 'break'
    - Timer counts down at the correct rate

    **Test shape:**
    - POST /settings { "break_duration_seconds": 600 }
    - POST /sessions/focus to start focus session
    - Simulate focus completion (or wait, or test-backend force-complete)
    - GET /sessions/current should return break session with status='running'
    - Verify remaining_seconds is approximately 600
    """
    # Note: This test assumes a settings endpoint exists. The contract says
    # settings are client-local (localStorage), but the backend may still
    # track them (or not). TBD: does the backend have a /settings endpoint?
    # For now, assuming no backend involvement per Contract-002.
    
    # If settings are client-only, we can't test this via HTTP.
    # This test will be reshaped once we clarify the contract.
    
    # Start a focus session
    response = client.post("/sessions/focus", json={})
    assert response.status_code == 201
    focus_session = response.json()
    assert focus_session["type"] == "focus"
    assert focus_session["status"] == "running"
    focus_session_id = focus_session["id"]
    
    # Simulate focus completion (test endpoint or manual elapsed-time advancement)
    response = client.post(
        f"/sessions/{focus_session_id}/complete",
        json={"elapsed_seconds": 1500}  # 25 minutes, standard focus duration
    )
    assert response.status_code == 200
    
    # After focus completes, a break session should exist
    # (Either auto-created on the backend, or the client should have POSTed it)
    response = client.get("/sessions/current")
    assert response.status_code == 200
    current_session = response.json()
    assert current_session["type"] == "break"
    assert current_session["status"] == "running"
    # Break duration is set to 600s
    assert current_session["remaining_seconds"] <= 600
    assert current_session["remaining_seconds"] > 0


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_adjusts_break_duration_mid_focus_and_new_duration_applies(
    client: TestClient,
):
    """
    **Scenario:** Keisha changes break duration while focus is running; new duration applies on transition

    Keisha starts a focus session with default break duration 300s. Midway through
    (say, 10 minutes into the 25-minute focus), she decides she needs longer breaks
    and changes the setting to 900s. When the focus session ends, the break timer
    should start with 900s, not 300s.

    **Observable:**
    - Initial break duration is 300s (or whatever default)
    - Focus session is running
    - Break duration setting is updated to 900s (client-side, via settings UI or test call)
    - Focus session completes
    - Break session starts with 900s remaining

    **Test shape:**
    - POST /sessions/focus (assumes default break_duration is tracked or passed)
    - Update break_duration (via settings API if it exists, or mock)
    - POST /sessions/{focus_id}/complete
    - GET /sessions/current
    - Verify break session has ~900s remaining, not 300s
    """
    # Start a focus session with the default break duration
    response = client.post("/sessions/focus", json={})
    assert response.status_code == 201
    focus_session = response.json()
    focus_session_id = focus_session["id"]
    
    # Assume we can update the break duration via a settings endpoint (TBD in contract)
    # For now, this is a placeholder. Contract-002 says settings are client-local,
    # so the backend might not have a PUT /settings endpoint.
    # If it doesn't, this test will be reshaped.
    
    # Complete the focus session
    response = client.post(
        f"/sessions/{focus_session_id}/complete",
        json={"elapsed_seconds": 600}  # 10 minutes
    )
    assert response.status_code == 200
    
    # Break session should exist with the updated duration (900s, not 300s)
    response = client.get("/sessions/current")
    assert response.status_code == 200
    break_session = response.json()
    assert break_session["type"] == "break"
    assert break_session["status"] == "running"
    # We expect ~900 seconds remaining
    # (The test will need to account for how settings are actually updated)


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_skips_break_and_goes_straight_to_next_focus(
    client: TestClient,
):
    """
    **Scenario:** Keisha skips a break mid-timer and transitions directly to focus

    Break timer is running. Keisha realizes she's not ready for a break yet
    (or doesn't need one) and taps "Skip Break". The break session is marked
    as skipped (not completed). The app goes idle or prompts for the next
    focus session. No notification fires.

    **Observable:**
    - Break session is running, status='running'
    - User taps "Skip Break"
    - Break session transitions to status='skipped'
    - Daily history records the break as skipped (not part of total break time)
    - No notification fires

    **Test shape:**
    - POST /sessions/focus
    - POST /sessions/{focus_id}/complete (auto-start break)
    - PATCH /sessions/{break_id} { "action": "skip" }
    - GET /sessions/{break_id}
    - Verify status='skipped'
    - GET /daily/summary
    - Verify break session does not contribute to daily break_minutes
    """
    # Start a focus session
    response = client.post("/sessions/focus", json={})
    assert response.status_code == 201
    focus_session_id = response.json()["id"]
    
    # Complete focus, which auto-starts break
    response = client.post(
        f"/sessions/{focus_session_id}/complete",
        json={"elapsed_seconds": 1500}
    )
    assert response.status_code == 200
    
    # Get the current (break) session
    response = client.get("/sessions/current")
    assert response.status_code == 200
    break_session = response.json()
    break_session_id = break_session["id"]
    assert break_session["type"] == "break"
    assert break_session["status"] == "running"
    
    # Skip the break
    response = client.patch(
        f"/sessions/{break_session_id}",
        json={"action": "skip"}
    )
    assert response.status_code == 200
    skipped = response.json()
    assert skipped["status"] == "skipped"
    
    # Verify daily summary doesn't count the skipped break toward total break time
    response = client.get("/daily/summary")
    assert response.status_code == 200
    summary = response.json()
    # If break was skipped, it should not be in break_minutes total
    # (Exact assertion depends on the summary schema)
    assert "break_minutes" in summary
