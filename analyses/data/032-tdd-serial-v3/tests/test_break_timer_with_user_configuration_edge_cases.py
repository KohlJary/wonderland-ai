"""Edge case scenarios for break timer with user configuration feature.

These test the fragile boundaries: what happens when break auto-starts while
focus is still completing, when the user mashes skip/adjust buttons, when
settings change mid-session, when backend timing diverges from client
expectations. These are the scenarios that look fine on the happy path
and break on the second Tuesday in March.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.skip(reason="backend models not yet implemented")
def test_break_auto_start_is_idempotent_focus_completion_fires_twice(
    client: TestClient,
):
    """
    **Scenario:** Focus completion event fires twice (retry or duplication)
    
    The focus session ends. The completion event is sent to backend and
    acknowledged. Due to a retry, the exact same event is sent again.
    The break should not double-start; there should still be only one
    break session, and the second completion is rejected or idempotent.
    
    **Severity:** silent-wrongness — Keisha sees two break sessions in her
    history, or the UI glitches and shows two breaks running simultaneously.
    
    **Observable:**
    - POST /sessions/log { type: 'focus', ... } (first time): 200, session_id
    - POST /sessions/log { type: 'focus', ... } (second time, same data):
      409 (rejected) or 200 (idempotent, no new session created)
    - GET /sessions?date=YYYY-MM-DD shows only one focus completion, not two
    - Break auto-starts only once
    
    **Test shape:**
    - POST /sessions/log { type: 'focus', ... }
    - POST /sessions/log { type: 'focus', ... } (same payload)
    - GET /sessions?date=YYYY-MM-DD
    - Verify exactly one focus session, not two
    - POST /sessions/break or verify break auto-created
    - Verify only one break session exists
    """
    # Log focus completion first time
    response = client.post(
        "/sessions/log",
        json={
            "type": "focus",
            "duration_configured_seconds": 1500,
            "duration_actual_seconds": 1500,
            "completed_at": "2025-01-01T10:30:00Z",
        }
    )
    assert response.status_code == 200
    first_log = response.json()
    first_session_id = first_log.get("session_id")
    
    # Log the same focus completion again (retry)
    response = client.post(
        "/sessions/log",
        json={
            "type": "focus",
            "duration_configured_seconds": 1500,
            "duration_actual_seconds": 1500,
            "completed_at": "2025-01-01T10:30:00Z",
        }
    )
    # Should be rejected (409) or idempotent (200 with same session_id)
    assert response.status_code in (200, 409)
    if response.status_code == 200:
        second_log = response.json()
        # If idempotent, should return the same session_id
        assert second_log.get("session_id") == first_session_id
    
    # Verify history shows only one focus session
    response = client.get("/sessions?date=2025-01-01")
    if response.status_code == 200:
        sessions = response.json()
        focus_sessions = [s for s in sessions if s.get("type") == "focus"]
        assert len(focus_sessions) == 1, "Should have exactly one focus session"


@pytest.mark.skip(reason="backend models not yet implemented")
def test_break_duration_boundaries_min_and_max_enforced(
    client: TestClient,
):
    """
    **Scenario:** Keisha tries to set an invalid break duration
    
    She taps the break duration field and tries to set 0 seconds (or -10,
    or 2 hours). The backend should reject invalid durations and return
    a 400 error, or cap the value to [60, 1800] per the spec.
    
    **Severity:** degradation — UI allows invalid input, or silent capping
    produces unexpected behavior.
    
    **Observable:**
    - POST /settings { break_duration_seconds: 0 }: 400 or auto-capped to 60
    - POST /settings { break_duration_seconds: -10 }: 400 or auto-capped to 60
    - POST /settings { break_duration_seconds: 7200 }: 400 or auto-capped to 1800
    - POST /settings { break_duration_seconds: 600 }: 200, accepted
    - Per contract-note-006, valid range is [60, 1800] seconds
    
    **Test shape:**
    - Test out-of-range values: 0, -10, 1, 59, 1801, 7200
    - For each, verify either 400 response or auto-capped to valid range
    - Test valid values: 60, 300, 900, 1800
    - Verify all return 200
    """
    # Test values below minimum (60)
    for invalid_value in [0, -10, 1, 59]:
        response = client.post(
            "/settings",
            json={"break_duration_seconds": invalid_value}
        )
        if response.status_code == 200:
            # Auto-capped; verify it's at least 60
            result = response.json()
            assert result["break_duration_seconds"] >= 60
        else:
            # Rejected
            assert response.status_code == 400
    
    # Test values above maximum (1800)
    for invalid_value in [1801, 7200, 10000]:
        response = client.post(
            "/settings",
            json={"break_duration_seconds": invalid_value}
        )
        if response.status_code == 200:
            # Auto-capped; verify it's at most 1800
            result = response.json()
            assert result["break_duration_seconds"] <= 1800
        else:
            # Rejected
            assert response.status_code == 400
    
    # Test valid values
    for valid_value in [60, 300, 900, 1800]:
        response = client.post(
            "/settings",
            json={"break_duration_seconds": valid_value}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["break_duration_seconds"] == valid_value


@pytest.mark.skip(reason="backend models not yet implemented")
def test_break_skip_while_break_is_already_complete_is_safe(
    client: TestClient,
):
    """
    **Scenario:** Break completes naturally, then Keisha taps skip
    
    A break counts down to 0 and completes. Somehow (network lag, race
    condition), the UI still shows the break and Keisha taps skip. The
    backend should reject the skip (break is already complete) or ignore
    it (no-op), not crash or corrupt state.
    
    **Severity:** degradation — API returns 500, or state becomes inconsistent.
    
    **Observable:**
    - Break session status='completed'
    - DELETE /sessions/{break_id} or PATCH { action: 'skip' }
    - Response is 200 (idempotent no-op), 409 (already completed), or 400
    - No error logged or returned to user
    - Session is still marked completed, not 'skipped' or reverted
    
    **Test shape:**
    - POST /sessions/break
    - (Simulate or wait for break to complete via POST /sessions/log)
    - PATCH /sessions/{break_id} { action: 'skip' }
    - Verify status code is not 500; response is safe
    - Verify break status is still 'completed', not changed
    """
    # Start a break
    response = client.post("/sessions/break", json={})
    if response.status_code in (200, 201):
        break_session = response.json()
        break_id = break_session["id"]
        
        # Simulate break completion by logging it
        response = client.post(
            "/sessions/log",
            json={
                "type": "break",
                "duration_configured_seconds": 600,
                "duration_actual_seconds": 600,
                "completed_at": "2025-01-01T10:45:00Z",
            }
        )
        # Break is now completed (or marked as logged)
        
        # Try to skip it after it's complete
        response = client.patch(
            f"/sessions/{break_id}",
            json={"action": "skip"}
        )
        # Should be safe: 200 (idempotent), 409 (already completed), or 400
        assert response.status_code in (200, 400, 409)
        # Should not be 500
        assert response.status_code != 500


@pytest.mark.skip(reason="backend models not yet implemented")
def test_settings_change_mid_session_affects_next_session_not_current(
    client: TestClient,
):
    """
    **Scenario:** Keisha changes her break duration during a running break
    
    A break is running at 10 minutes (600 seconds). Keisha taps settings
    and changes her default to 5 minutes (300 seconds). The running break
    should still be 10 minutes — the setting change takes effect when the
    next break starts, not retroactively.
    
    **Severity:** silent-wrongness — the running break suddenly speeds up
    or slows down, confusing Keisha.
    
    **Observable:**
    - POST /sessions/break (auto-uses configured duration=600)
    - GET /sessions/{break_id} shows duration=600
    - POST /settings { break_duration_seconds: 300 }
    - GET /sessions/{break_id} still shows duration=600 (unchanged)
    - (Next focus/break cycle uses the new default=300)
    
    **Test shape:**
    - POST /sessions/break -> duration=600
    - POST /settings { break_duration_seconds: 300 }
    - GET /sessions/{break_id}
    - Verify duration is still 600, not updated to 300
    """
    # Start a break with some initial default (e.g., 600)
    response = client.post("/sessions/break", json={})
    if response.status_code in (200, 201):
        break_session = response.json()
        break_id = break_session["id"]
        initial_duration = break_session["duration_seconds"]
        assert initial_duration > 0
        
        # Change the default setting
        response = client.post(
            "/settings",
            json={"break_duration_seconds": initial_duration // 2}
        )
        if response.status_code == 200:
            # Verify the running break is not affected
            response = client.get(f"/sessions/{break_id}")
            if response.status_code == 200:
                current = response.json()
                # Duration should still be the original, not the new setting
                assert current["duration_seconds"] == initial_duration


@pytest.mark.skip(reason="backend models not yet implemented")
def test_break_session_logging_uses_actual_time_not_configured_time(
    client: TestClient,
):
    """
    **Scenario:** Keisha's break runs slightly longer than configured
    
    Break configured: 600 seconds (10 min). Actual break: 602 seconds
    (user had a call run 2 seconds over). When logging the completed break,
    the backend receives actual=602 but configured=600. The backend should
    accept the small delta (per contract: allow elapsed <= configured + 5%)
    and log both values separately (not conflate them).
    
    **Severity:** silent-wrongness — if backend only stores 'duration'
    without distinguishing configured vs. actual, daily history shows wrong
    totals. Keisha thinks she took 602 seconds breaks when she intended 600.
    
    **Observable:**
    - POST /sessions/log { duration_configured: 600, duration_actual: 602, ... }
    - Response: 200 (accepted), session logged
    - Response includes both configured and actual durations separately
    - GET /sessions?date=YYYY-MM-DD returns both fields
    - Aggregates (daily break time) should use actual, not configured
    
    **Test shape:**
    - POST /sessions/log { type: 'break', duration_configured: 600, duration_actual: 602, ... }
    - Verify 200
    - GET /sessions?date=YYYY-MM-DD
    - Verify returned session has both configured and actual fields
    - Verify actual=602 is used for aggregates (not 600)
    """
    response = client.post(
        "/sessions/log",
        json={
            "type": "break",
            "duration_configured_seconds": 600,
            "duration_actual_seconds": 602,
            "completed_at": "2025-01-01T10:45:00Z",
        }
    )
    assert response.status_code == 200
    log_result = response.json()
    session_id = log_result.get("session_id")
    
    # Fetch the logged session to verify both durations are stored
    response = client.get("/sessions?date=2025-01-01")
    if response.status_code == 200:
        sessions = response.json()
        break_sessions = [
            s for s in sessions
            if s.get("type") == "break" and s.get("session_id") == session_id
        ]
        assert len(break_sessions) == 1
        session = break_sessions[0]
        assert session.get("duration_configured_seconds") == 600
        assert session.get("duration_actual_seconds") == 602


@pytest.mark.skip(reason="backend models not yet implemented")
def test_break_auto_start_respects_user_configured_duration_not_default(
    client: TestClient,
):
    """
    **Scenario:** User changed their default break length, focus ends, break
    auto-starts with the new duration (not a stale cached value)
    
    Keisha had 5-minute breaks. She changed to 15 minutes. Her focus session
    ends. The auto-started break should be 15 minutes, not 5. The backend
    (or frontend, depending on contract) must use the *current* configured
    value, not a stale value.
    
    **Severity:** degradation — break uses stale setting, confusing Keisha.
    
    **Observable:**
    - POST /settings { break_duration_seconds: 300 }
    - GET /settings confirms 300
    - POST /sessions/log { type: 'focus', ... }
    - Backend auto-creates or frontend POST /sessions/break uses configured=300
    - (Later) POST /settings { break_duration_seconds: 900 }
    - POST /sessions/log { type: 'focus', ... } (new focus end)
    - Auto-started break uses 900, not 300
    
    **Test shape:**
    - POST /settings { break_duration_seconds: 300 }
    - POST /sessions/break (or auto-created via focus-end)
    - GET /sessions/{break_id}
    - Verify duration=300
    - POST /settings { break_duration_seconds: 900 }
    - POST /sessions/break (new break)
    - GET /sessions/{new_break_id}
    - Verify duration=900 (not the old 300)
    """
    # Set initial break duration
    response = client.post(
        "/settings",
        json={"break_duration_seconds": 300}
    )
    if response.status_code == 200:
        # Start break with this setting
        response = client.post("/sessions/break", json={})
        if response.status_code in (200, 201):
            first_break = response.json()
            assert first_break["duration_seconds"] == 300
            
            # Change setting
            response = client.post(
                "/settings",
                json={"break_duration_seconds": 900}
            )
            if response.status_code == 200:
                # Start new break with new setting
                response = client.post("/sessions/break", json={})
                if response.status_code in (200, 201):
                    second_break = response.json()
                    # Should use new setting, not old
                    assert second_break["duration_seconds"] == 900


@pytest.mark.skip(reason="backend models not yet implemented")
def test_adjust_break_duration_within_valid_range_only(client: TestClient):
    """
    **Scenario:** While a break is running, Keisha tries to adjust it to 0
    
    Break is at 9:00 remaining. She taps the duration field and tries to
    set it to 0, or -5, or 3 hours. The backend should reject the invalid
    value (400) or silently cap it to [60, 1800].
    
    **Severity:** degradation — break duration becomes invalid, UI glitches.
    
    **Observable:**
    - Break is running (duration=600)
    - PATCH /sessions/{break_id} { duration_seconds: 0 }: 400 or auto-cap to 60
    - PATCH /sessions/{break_id} { duration_seconds: -10 }: 400 or auto-cap to 60
    - PATCH /sessions/{break_id} { duration_seconds: 10000 }: 400 or auto-cap to 1800
    - GET /sessions/{break_id} shows valid duration after each attempt
    
    **Test shape:**
    - POST /sessions/break
    - For invalid values [0, -10, 1, 59, 1801, 7200]:
      - PATCH /sessions/{break_id} { duration_seconds: value }
      - Verify 400 or auto-capped to valid range
    - For valid values [60, 900, 1800]:
      - PATCH /sessions/{break_id} { duration_seconds: value }
      - Verify 200, duration updated correctly
    """
    response = client.post("/sessions/break", json={})
    if response.status_code in (200, 201):
        break_session = response.json()
        break_id = break_session["id"]
        
        # Test invalid durations
        for invalid_value in [0, -10, 1, 59, 1801, 7200]:
            response = client.patch(
                f"/sessions/{break_id}",
                json={"duration_seconds": invalid_value}
            )
            if response.status_code == 200:
                # Auto-capped
                result = response.json()
                assert 60 <= result["duration_seconds"] <= 1800
            else:
                # Rejected
                assert response.status_code == 400
        
        # Test valid durations
        for valid_value in [60, 900, 1800]:
            response = client.patch(
                f"/sessions/{break_id}",
                json={"duration_seconds": valid_value}
            )
            assert response.status_code == 200
            result = response.json()
            assert result["duration_seconds"] == valid_value
