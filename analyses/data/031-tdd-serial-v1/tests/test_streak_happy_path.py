"""Test: Kenji completes sessions consistently and watches his streak grow.

User journey for story-005 (Kenji wants to see weekly session count as motivation).
Focus Session Timer is already implemented; this tests the streak calculation
and display on top of the event log (Feature 005).

The happy path: user opens the app on Monday, completes one session per day
M-W, checks the daily review on Wednesday and sees 3 sessions this week.
On Thursday, completes another session. On Friday opens the app but doesn't
complete any session. On Saturday opens the app, completes a session, and
sees the streak is updated (depending on whether Friday's skip breaks the streak).

BLOCKER:
- All tests are blocked on Feature 003 event log implementation.
  Once Feature 003 is complete and provides a fixture to insert test data,
  these tests can unskip and run against actual event log queries.

UNRESOLVED CONTRACT:
- Scenario 005-B (daily streak vs. weekly count): These tests assume we're tracking
  a daily consecutive-days streak. If the contract resolves to "weekly count only"
  (no daily streak), these tests will need rewriting.
"""

import pytest
from datetime import datetime, timedelta, timezone


def test_kenji_completes_three_sessions_in_a_week_sees_count_on_review(client, db_session):
    """
    Scenario 005-A: Kenji completes one focus session on Monday, Tuesday, and Wednesday.
    When he opens the daily review on Wednesday evening, he sees "3 sessions this week"
    (or similar language). The count is displayed prominently and gives him a sense of momentum.
    
    Acceptance criteria:
    - Weekly session count is displayed on the daily review
    - Count shows 3 (for M-T-W sessions)
    - If also displaying daily streak: "3-day streak" (consecutive days)
    - UI is motivating, not judgmental
    
    BLOCKED: Feature 003 event log insertion fixture pending.
    """
    # PRECONDITION: Kenji has focus sessions (Feature 001) working.
    # PRECONDITION: Event log (Feature 003) is logging completed sessions.
    
    # Monday, user completes one session.
    monday_midnight = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)  # ISO week 1, Monday
    
    # Simulate completing a session on Monday.
    # (In M5, Tweedledum will implement the event-log write; this test
    # uses the fixture to insert test data once the schema exists.)
    
    pytest.skip("Feature 003 event log insertion fixture not yet implemented; test data insertion fixture pending.")


def test_weekly_count_resets_on_monday(client, db_session):
    """
    Scenario 005-D: Kenji completes 5 sessions in week 1 (Jan 1-7). On Monday of week 2,
    the weekly counter shows 0. When he completes one session on Monday week 2,
    the counter shows 1 (not 6).
    
    Acceptance criteria:
    - Weekly session count resets at Monday 00:00 (ISO week boundary)
    - Count does not accumulate across weeks
    - User sees "0 sessions this week" on Monday morning (before completing a session)
    - After completing Monday's session, count shows "1"
    
    BLOCKED: Feature 003 event log insertion fixture + timezone handling.
    """
    pytest.skip("Feature 003 event log insertion fixture not yet implemented; weekly aggregation query pending.")


def test_daily_streak_vs_weekly_count_are_separate(client, db_session):
    """
    CLARIFICATION NEEDED: Contract Note 005 is ambiguous about whether this
    feature is:
    (a) A daily streak (consecutive days with ≥1 session), OR
    (b) A weekly session count (reset every Monday)
    
    Story 005 says "weekly session count" but the contract note mentions
    "consecutive days" which sounds like daily streak. This test is a
    placeholder until Tweedledee and Tweedledum resolve the contract.
    
    If it's (a), the test is: complete sessions Mon, Tue, skip Wed, complete
    Thu — streak should be broken (Wed was skipped), so 1 day (Thursday only).
    
    If it's (b), the test is: same actions, weekly count shows 3 (M, T, Th).
    
    Current test: SKIP until contract resolves.
    
    BLOCKED: Contract Note 005 ambiguity on daily streak vs. weekly count.
    """
    pytest.skip("Contract Note 005 ambiguity: daily streak vs. weekly count. Awaiting Tweedledee/Tweedledum resolution.")
