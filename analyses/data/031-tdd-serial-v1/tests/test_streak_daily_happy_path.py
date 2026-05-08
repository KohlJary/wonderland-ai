"""
Happy-path scenario for daily streak (Feature 005, interpretation: Derek's daily streak).

Derek completes sessions on three consecutive days and sees a streak counter.
On the fourth day with no completion, the streak resets.

PRECONDITION: Feature 001 (focus session timer) and Feature 003 (event log)
are implemented. This test depends on:
- POST /api/sessions/start (Feature 001)
- POST /api/sessions/{id}/complete or similar (Feature 003)
- GET /api/daily-review?date=YYYY-MM-DD (Feature 003)

Tests will fail until Feature 005 backend adds:
- GET /api/streak (returns current streak)
- Daily review augmented with streak field
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestStreakDailyHappyPath:
    """Derek's story: daily streak with reset on missed day."""

    def test_first_session_creates_streak_of_one(self, client, db_session):
        """
        Derek completes his first session ever on Monday.
        Streak should show 1 (one consecutive day with a session).
        """
        pytest.skip(
            "Feature 005 backend not yet implemented. "
            "Requires GET /api/streak endpoint and session completion logging."
        )
        # Expected API shape:
        # POST /api/sessions/start -> {session_id, ...}
        # POST /api/sessions/{id}/complete -> session is logged
        # GET /api/streak -> {streak_days: 1, last_completion_date: "2024-01-01"}

    def test_consecutive_days_increment_streak(self, client, db_session):
        """
        Derek completes a session Monday, Tuesday, Wednesday.
        After Wednesday completion, streak should show 3.
        """
        pytest.skip(
            "Feature 005 backend not yet implemented. "
            "Requires multi-day session logging and streak calculation."
        )

    def test_missing_a_day_resets_streak_to_zero(self, client, db_session):
        """
        Derek completes sessions Mon, Tue, Wed (streak=3).
        Thursday passes with no session.
        On Thursday evening, streak shows 0 (broken).
        """
        pytest.skip(
            "Feature 005 backend not yet implemented. "
            "Requires calculation: if (today - last_completion_date > 1 day) then streak=0."
        )

    def test_resuming_after_missed_day_starts_new_streak(self, client, db_session):
        """
        Derek's streak breaks on Thursday (no session).
        Friday he completes a session.
        Streak should show 1 (new streak started), not 4 (continuation of old).
        """
        pytest.skip(
            "Feature 005 backend not yet implemented. "
            "Requires logic: if streak was broken, first session after break starts streak=1."
        )
