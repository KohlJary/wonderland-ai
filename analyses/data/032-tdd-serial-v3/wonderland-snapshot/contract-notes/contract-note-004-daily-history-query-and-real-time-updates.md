## Contract Note 004: Daily history query and real-time updates

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None. Ticket-005 builds a view that displays today's sessions; no contract exists yet on how the frontend fetches them.

**Proposed Change:**

Define the query contract for session history. (1) What does the endpoint look like? (GET /sessions?date=2024-01-15?) (2) What does the response schema include? (3) How does the frontend stay in sync if new sessions complete while the history view is open (polling vs. events)?

**Source:** Ticket-005 (build history view) and Ticket-004 (log sessions). Story-003 (Dmitri) needs to see sessions update without refreshing the page.

**Frontend Impact (Tweedledee):**

Per contract-note 007, frontend polls GET /sessions?date=YYYY-MM-DD every 10s while the history view is visible. No WebSocket/events for v1. I calculate all aggregates (total focus time, session counts) from the response. The polling window is 10s; faster feels chatty, slower feels stale. I can adjust if you have a preference. On timezone: I'll send my local date as YYYY-MM-DD; you clarify in the contract whether this is UTC or local-time (affects midnight boundaries for users in non-UTC zones). Should I send timezone offset so you can normalize, or do you prefer I always send UTC?

**Backend Impact (Tweedledum):**

I design a GET /sessions/today endpoint that returns { date, focusSessions: [...], breakSessions: [...], totals: { totalFocusMinutes, totalBreakMinutes, focusCount, breakCount } }. I ensure the query is fast (indexed by date). If real-time updates are needed, I either: (a) expose polling, or (b) emit events that the frontend can subscribe to. I also need to decide: does 'today' respect the user's timezone, or UTC?
