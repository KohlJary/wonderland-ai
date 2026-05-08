"""User journey scenarios for daily review feature.

This test file exercises the daily review feature from Dmitri's standpoint:
he can see completed focus sessions from today, with accurate counts and
totals, and can compare to yesterday's productivity.

The scenarios test the GET /sessions?date=... endpoint and the aggregation behavior.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


def test_dmitri_views_daily_summary_with_completed_focus_sessions(client: TestClient):
    """
    **Scenario:** Dmitri opens daily review and sees completed focus sessions
    from today with accurate aggregates.
    
    Dmitri has completed 6 focus sessions today (25 min each, or varied durations).
    He also has 4 break sessions completed. He opens the daily summary view
    and sees the count of sessions and total focus time.
    
    **Observable:**
    - GET /sessions?date=YYYY-MM-DD returns all completed sessions for that day
    - Frontend displays: 'Completed focus sessions: 6', 'Total focus time: 145 minutes'
    - Each session shows type, timestamp, actual duration
    - The display is accurate and not inflated by abandoned sessions
    """
    # Generate today's date in ISO format
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Log multiple sessions with various durations
    sessions_to_log = [
        {"type": "focus", "duration_configured_seconds": 1500, "duration_actual_seconds": 1500},
        {"type": "break", "duration_configured_seconds": 300, "duration_actual_seconds": 300},
        {"type": "focus", "duration_configured_seconds": 1500, "duration_actual_seconds": 1480},
        {"type": "break", "duration_configured_seconds": 300, "duration_actual_seconds": 300},
        {"type": "focus", "duration_configured_seconds": 1500, "duration_actual_seconds": 1500},
        {"type": "break", "duration_configured_seconds": 300, "duration_actual_seconds": 290},
        {"type": "focus", "duration_configured_seconds": 1500, "duration_actual_seconds": 1500},
        {"type": "break", "duration_configured_seconds": 300, "duration_actual_seconds": 300},
        {"type": "focus", "duration_configured_seconds": 1500, "duration_actual_seconds": 1500},
        {"type": "break", "duration_configured_seconds": 300, "duration_actual_seconds": 310},
    ]
    
    # Log each session
    now = datetime.now(timezone.utc)
    for i, session_data in enumerate(sessions_to_log):
        completed_at = (now - timedelta(seconds=len(sessions_to_log) * 60 - i * 60)).isoformat()
        response = client.post(
            "/api/sessions/log",
            json={
                **session_data,
                "completed_at": completed_at,
            }
        )
        assert response.status_code == 200
        assert "session_id" in response.json()
    
    # Query today's sessions
    response = client.get(f"/api/sessions?date={today}")
    
    # Backend should return 200 OK
    assert response.status_code == 200
    data = response.json()
    
    # Response should include a list of sessions
    sessions = data.get("sessions", [])
    assert len(sessions) == 10, f"Expected 10 sessions, got {len(sessions)}"
    
    # Count focus and break sessions
    focus_sessions = [s for s in sessions if s["type"] == "focus"]
    break_sessions = [s for s in sessions if s["type"] == "break"]
    
    assert len(focus_sessions) == 6
    assert len(break_sessions) == 4
    
    # Verify response shape
    for session in sessions:
        assert "session_id" in session
        assert "type" in session
        assert session["type"] in ("focus", "break")
        assert "duration_actual_seconds" in session
        assert "duration_configured_seconds" in session
        assert "completed_at" in session
    
    # Verify aggregates
    totals = data.get("totals", {})
    assert "focus_count" in totals
    assert "break_count" in totals
    assert "focus_minutes" in totals
    assert "break_minutes" in totals
    
    assert totals["focus_count"] == 6
    assert totals["break_count"] == 4
    
    # Verify aggregates match session data
    expected_focus_seconds = sum(s["duration_actual_seconds"] for s in focus_sessions)
    expected_focus_minutes = expected_focus_seconds // 60
    assert totals["focus_minutes"] == expected_focus_minutes


def test_dmitri_compares_today_and_yesterday_without_confusion(client: TestClient):
    """
    **Scenario:** Dmitri sees today's summary (6 sessions) and yesterday's (4 sessions)
    side by side, without mixing them up.
    
    The two summaries are visually distinct and the counts do not cross-contaminate.
    If the view is refreshed or polling updates, the counts remain accurate.
    
    **Observable:**
    - GET /sessions?date=<today> returns today's sessions
    - GET /sessions?date=<yesterday> returns yesterday's sessions
    - The two queries return disjoint sets of sessions
    - Frontend displays both clearly labeled
    """
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    
    today_str = today.isoformat()
    yesterday_str = yesterday.isoformat()
    
    # Log sessions for today
    now = datetime.now(timezone.utc)
    for i in range(3):
        completed_at = (now - timedelta(seconds=i * 60)).isoformat()
        response = client.post(
            "/api/sessions/log",
            json={
                "type": "focus" if i % 2 == 0 else "break",
                "duration_configured_seconds": 1500 if i % 2 == 0 else 300,
                "duration_actual_seconds": 1500 if i % 2 == 0 else 300,
                "completed_at": completed_at,
            }
        )
        assert response.status_code == 200
    
    # Log sessions for yesterday
    yesterday_noon = datetime.combine(yesterday, datetime.min.time()).replace(tzinfo=timezone.utc, hour=12)
    for i in range(2):
        completed_at = (yesterday_noon - timedelta(seconds=i * 60)).isoformat()
        response = client.post(
            "/api/sessions/log",
            json={
                "type": "focus" if i % 2 == 0 else "break",
                "duration_configured_seconds": 1500 if i % 2 == 0 else 300,
                "duration_actual_seconds": 1500 if i % 2 == 0 else 300,
                "completed_at": completed_at,
            }
        )
        assert response.status_code == 200
    
    # Query today
    response_today = client.get(f"/api/sessions?date={today_str}")
    assert response_today.status_code == 200
    today_data = response_today.json()
    today_sessions = today_data.get("sessions", [])
    
    # Query yesterday
    response_yesterday = client.get(f"/api/sessions?date={yesterday_str}")
    assert response_yesterday.status_code == 200
    yesterday_data = response_yesterday.json()
    yesterday_sessions = yesterday_data.get("sessions", [])
    
    # The sessions should be disjoint (no session appears in both lists)
    today_ids = {s["session_id"] for s in today_sessions}
    yesterday_ids = {s["session_id"] for s in yesterday_sessions}
    assert len(today_ids & yesterday_ids) == 0, "Sessions appear in both today and yesterday"
    
    # Verify counts
    assert len(today_sessions) == 3
    assert len(yesterday_sessions) == 2
    
    # Verify all sessions in today's list have completed_at in today's range
    for session in today_sessions:
        completed_at_str = session["completed_at"]
        completed_at = datetime.fromisoformat(completed_at_str)
        completed_date = completed_at.date()
        assert completed_date == today, f"Session completed_at {completed_at_str} is not today"
    
    # Verify all sessions in yesterday's list have completed_at in yesterday's range
    for session in yesterday_sessions:
        completed_at_str = session["completed_at"]
        completed_at = datetime.fromisoformat(completed_at_str)
        completed_date = completed_at.date()
        assert completed_date == yesterday, f"Session completed_at {completed_at_str} is not yesterday"
