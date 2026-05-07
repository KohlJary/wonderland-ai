## Story 009: Feature 002 Happy Path — Jordan reviews today's count and history

**Feature:** Review session history and persistence across restarts (feature-002)

**Persona:** Jordan, 26, a student and gig worker who uses pomodoros to track productivity and feels scattered without evidence.

**Happy-path scenario:**

1. It's evening. Jordan opens the app. On the home screen, a prominent card displays "Today: 6 sessions / 150 minutes." Below that, "History" link is visible.

2. Jordan taps "History." A new screen opens showing three tabs: "Today," "This Week," "All-time."

3. The "This Week" tab is selected and shows a 7-day grid. Today (Wednesday) displays "6 sessions / 150 min." Yesterday (Tuesday) shows "5 sessions / 125 min." Earlier days show 0 or partial numbers. At the top, aggregates display: "This week: 34 sessions / 850 minutes."

4. Jordan taps "All-time." A summary card appears: "Total: 847 sessions / 21,175 minutes" (about 353 hours over several months). Below that, a scrollable list of weekly breakdown rows shows the pattern over time — some weeks with 40+ sessions, recent weeks with fewer (summer was busier than now).

5. Jordan closes the app while reviewing.

6. Jordan opens the app the next day. The home screen updates to show "Today: 0 sessions / 0 minutes" and "Yesterday: 6 sessions / 150 minutes." The history is intact; 'today' reset at midnight.

7. Jordan opens a new session, lets it run for 5 minutes, then closes the app mid-session (accidental). One hour later, they open the app again.

8. The home screen shows a recovery prompt: "You have an interrupted session from 1 hour ago. Complete as-is or discard?" Jordan taps "Discard." The session doesn't count toward today's total.

9. Jordan starts a fresh session and completes it normally. The home screen updates to reflect "Today: 1 session / 25 minutes."

**Expected result:**

Jordan sees evidence of work accumulated over time. Session history is persistent across app restarts (unless explicitly discarded). Today's count resets at midnight. Interrupted sessions are recoverable but don't corrupt the history.

**Contract assumptions validated:**

- History queries (window=today, week, all-time) return pre-aggregated totals.
- Session records are immutable (written once, never edited).
- App restart doesn't lose in-progress sessions (stored in localStorage).
- State recovery on restart is user-driven (user chooses to complete or discard).
