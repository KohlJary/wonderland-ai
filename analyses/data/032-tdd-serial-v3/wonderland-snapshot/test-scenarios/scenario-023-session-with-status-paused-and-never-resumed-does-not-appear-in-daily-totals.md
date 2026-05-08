## Scenario 023: Session with status='paused' and never resumed does not appear in daily totals

**Severity:** silent-wrongness

**Setup:**

Dmitri started a focus session at 10:00 UTC, ran it for 8 minutes, paused it at 10:08 UTC. He never resumed it. He also completed four other full focus sessions. The backend has a row for the paused session with status='paused'. The backend logs completed sessions in a separate completed-sessions table or marks status='completed'.

**Trigger:**

Frontend queries GET /sessions?date=2024-01-15. Backend queries for sessions where status='completed'.

**Expected:**

The response includes 4 focus sessions (the completed ones) and does not include the paused session. Daily total: 4 sessions, not 5.

**Concern:**

The backend query might not filter on status, returning all sessions regardless of state. The schema might not distinguish 'paused' from 'completed', treating them the same. Paused sessions might be auto-completed on some timeout, silently inflating the count.

**Property:**

GET /sessions?date=D returns only sessions where status='completed'. For any query, count(returned sessions with status='paused') = 0.

**Implies:**
- Implies backend must have a status field on session records and must filter status='completed' before returning.
