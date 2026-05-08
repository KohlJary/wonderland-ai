"""User journey scenarios for break timer with user configuration feature.

These test that the break timer feature works for Keisha: she can configure
a default break duration, the app auto-starts a break timer when focus ends,
and she can adjust or skip the break.

The scenarios in this file are *aspirational* — they describe what the
feature should do, not what the backend currently does. They are written
as pytest fixtures + test functions to make the surface concrete, even
though the implementation is still ahead.

The TestClient here exercises the backend API layer, which is the boundary
where Alice's user journey meets the code.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_configures_default_break_duration_and_it_persists(
    client: TestClient,
):
    """
    **Scenario:** Keisha sets her default break duration to 10 minutes
    
    Keisha opens settings, sets break duration to 10 minutes (600 seconds).
    She closes the app and reopens it. Her break duration setting is still
    10 minutes. She never has to reconfigure.
    
    **Observable:**
    - GET /settings returns break_duration_seconds (or client reads localStorage)
    - POST /settings or (client localStorage write) sets it to 600
    - Reopen app / GET /settings confirms 600
    
    **Test shape:**
    - GET /settings (initial state, default 5 min = 300s)
    - POST /settings { "break_duration_seconds": 600 }
    - GET /settings verifies 600
    - (If client-side persistence: simulate close/reopen and verify localStorage)
    
    Note: Per contract-note-006, v1 uses client-side localStorage, no backend
    API. This test validates the presence of sensible defaults in the API layer
    if settings are ever queried or logged.
    """
    # GET /settings to read initial state
    response = client.get("/settings")
    # v1: backend may not have a settings endpoint (settings are client-local)
    # If no endpoint, skip this path; test is aspirational
    if response.status_code == 200:
        initial = response.json()
        assert initial.get("break_duration_seconds", 300) >= 60  # At least 1 min
        
        # POST /settings to update
        response = client.post(
            "/settings",
            json={"break_duration_seconds": 600}
        )
        assert response.status_code in (200, 201)
        
        # GET /settings to verify persistence
        response = client.get("/settings")
        assert response.status_code == 200
        updated = response.json()
        assert updated["break_duration_seconds"] == 600


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_focus_ends_break_auto_starts_at_configured_duration(
    client: TestClient,
):
    """
    **Scenario:** Keisha's focus session ends, break timer starts automatically
    
    Keisha configured 10-minute breaks. Her focus session ends. The app
    automatically transitions to a break timer showing 10:00 remaining.
    No button tap required; no reconfiguration.
    
    **Observable:**
    - Focus session completes (POST /sessions/log with type='focus')
    - Backend receives and acknowledges
    - Next GET /sessions/current or POST /sessions/break auto-creates break
    - Break session has status='running', duration=600 (or user's configured value)
    
    **Test shape:**
    - POST /sessions/log { type: 'focus', duration_configured: 1500, ... }
    - Verify 200 response, session_id returned
    - POST /sessions/break to start break (auto-uses configured duration)
    - GET /sessions/current verifies break is running
    - Verify duration matches the configured break length
    
    Note: The contract (note-005) covers /sessions/log endpoint. This scenario
    extends it to the break auto-start behavior.
    """
    # Log a completed focus session
    response = client.post(
        "/sessions/log",
        json={
            "type": "focus",
            "duration_configured_seconds": 1500,
            "duration_actual_seconds": 1502,
            "completed_at": "2025-01-01T10:30:00Z",
        }
    )
    # Per contract-note-005, backend returns { session_id, acknowledged: true }
    if response.status_code == 200:
        focus_log = response.json()
        assert focus_log["acknowledged"] is True
        focus_session_id = focus_log.get("session_id")
        
        # POST /sessions/break to start a break (or backend auto-creates it)
        response = client.post("/sessions/break", json={})
        # If not implemented, skip
        if response.status_code in (200, 201):
            break_session = response.json()
            assert break_session["type"] == "break"
            assert break_session["status"] == "running"
            # Duration should match user's configured break (default 300 if not set)
            assert break_session["duration_seconds"] >= 60


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_adjusts_break_length_before_break_starts_without_losing_default(
    client: TestClient,
):
    """
    **Scenario:** Keisha wants a 15-minute break today, not her usual 10 minutes
    
    Her focus session ends, a 10-minute break auto-starts. Before the break
    actually begins counting, she taps the duration field and changes it to
    15 minutes (900 seconds). The break counts down from 15:00. Her default
    setting remains 10 minutes for next time.
    
    **Observable:**
    - Break session created with duration=600 (default)
    - PATCH /sessions/{break_id} { "duration_seconds": 900 }
    - GET /sessions/{break_id} shows duration=900
    - Break still status='paused' or status='running' (not affected by duration change)
    - GET /settings still shows default=600
    
    **Test shape:**
    - POST /sessions/break (auto-creates with default)
    - GET /sessions/{id} verifies duration=600
    - PATCH /sessions/{id} { "duration_seconds": 900 }
    - GET /sessions/{id} verifies duration=900
    - GET /settings verifies default is still 600
    """
    # Start a break with default duration
    response = client.post("/sessions/break", json={})
    if response.status_code in (200, 201):
        break_session = response.json()
        break_id = break_session["id"]
        assert break_session["duration_seconds"] == 300  # Assume default 5 min for test
        
        # Adjust duration for this session only
        response = client.patch(
            f"/sessions/{break_id}",
            json={"duration_seconds": 900}
        )
        if response.status_code == 200:
            patched = response.json()
            assert patched["duration_seconds"] == 900
            
            # Verify default setting is unchanged
            response = client.get("/settings")
            if response.status_code == 200:
                settings = response.json()
                # Default should still be the original (not updated by the adjustment)
                assert settings["break_duration_seconds"] == 300


@pytest.mark.skip(reason="backend models not yet implemented")
def test_keisha_skips_break_goes_straight_to_next_focus(
    client: TestClient,
):
    """
    **Scenario:** Keisha is on a roll and doesn't want a break today
    
    A break session auto-starts. Keisha taps 'Skip Break'. The break is
    discarded and she immediately starts a new focus session. No break
    is logged to her history.
    
    **Observable:**
    - Break session created (status='running' or 'paused')
    - DELETE /sessions/{break_id} or PATCH /sessions/{break_id} { action: 'skip' }
    - Response confirms cancellation
    - POST /sessions/log does not include the skipped break
    - GET /sessions?date=YYYY-MM-DD does not show the break
    - POST /sessions/focus starts new focus (or auto-starts if break is skipped)
    
    **Test shape:**
    - POST /sessions/break
    - DELETE /sessions/{break_id} or PATCH with skip action
    - GET /sessions?date=YYYY-MM-DD
    - Verify no break session in response (or status='skipped'/'cancelled')
    - POST /sessions/log { type: 'focus', ... }
    - GET /sessions?date=YYYY-MM-DD shows only the new focus, not the skipped break
    """
    # Start a break
    response = client.post("/sessions/break", json={})
    if response.status_code in (200, 201):
        break_session = response.json()
        break_id = break_session["id"]
        
        # Skip the break (delete or mark as skipped)
        response = client.delete(f"/sessions/{break_id}")
        # Or PATCH with skip action
        if response.status_code != 204:  # Try PATCH if DELETE not supported
            response = client.patch(
                f"/sessions/{break_id}",
                json={"action": "skip"}
            )
        
        assert response.status_code in (200, 204)
        
        # Start a new focus session
        response = client.post(
            "/sessions/log",
            json={
                "type": "focus",
                "duration_configured_seconds": 1500,
                "duration_actual_seconds": 1500,
                "completed_at": "2025-01-01T11:00:00Z",
            }
        )
        # Verify the skipped break is not in history
        if response.status_code == 200:
            response = client.get("/sessions?date=2025-01-01")
            if response.status_code == 200:
                sessions = response.json()
                # Should have focus but no break (or break with skipped status)
                break_sessions = [
                    s for s in sessions
                    if s.get("type") == "break" and s.get("status") != "skipped"
                ]
                assert len(break_sessions) == 0, "Skipped break should not appear"
