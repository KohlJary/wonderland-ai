## Contract Note 003: Event Log and Daily Review Query (Feature 003)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none

**Proposed Change:**

All completed sessions (focus and break) are logged to an event log with timestamp and completion status. Daily review queries this log by date (midnight-to-midnight boundary) and aggregates: count of completed focus sessions, count of completed breaks, count of skipped breaks, total focus time (sum of durations for completed focus sessions). Query is readable by frontend, not writable.

**Source:** story-003 (David wants: completed session count, break adherence, total focus time, with daily rollover at midnight)

**Frontend Impact (Tweedledee):**

UI has a daily review screen that displays aggregated stats (read from query). Stats must update in real-time as sessions complete (not only when user manually refreshes). Daily boundary must cross at midnight (rolling window, not calendar day — if user is in PT and it's 11:59pm, next session completing after midnight belongs to tomorrow's count). UI displays 'completed' vs 'skipped' break counts separately so user can see adherence.

**Backend Impact (Tweedledum):**

Backend stores event log (timestamp, type, duration_ms, session_id). Daily review query aggregates by calendar date (midnight-to-midnight, using user's local midnight — needs client to send timezone or we default to UTC). Query counts: (completed focus sessions), (completed breaks), (skipped breaks), (sum of durations for completed focus only). Real-time updates: frontend polls or WebSocket-subscribes to the event log; backend emits new events as they arrive. Invariant: each session_id appears exactly once in the log (either as 'completed' or 'skipped', never both). Open question: what happens if user completes a session, then loses network — does client retry logging? If client closes before log lands, is the session lost (acceptable for v1?) or do we need on-device buffering?
