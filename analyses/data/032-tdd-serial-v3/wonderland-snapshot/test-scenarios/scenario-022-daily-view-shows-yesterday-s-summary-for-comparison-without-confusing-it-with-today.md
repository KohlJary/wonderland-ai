## Scenario 022: Daily view shows yesterday's summary for comparison without confusing it with today

**Severity:** degradation

**Setup:**

Today is 2024-01-15. Dmitri completed 6 focus sessions today. Yesterday (2024-01-14) he completed 4 focus sessions. The view displays both.

**Trigger:**

Dmitri scrolls down or taps 'Yesterday' to see the prior day's count. The view makes a second query: GET /sessions?date=2024-01-14.

**Expected:**

The two summaries are visually distinct (e.g., labeled 'Today: 6 sessions' and 'Yesterday: 4 sessions'). The numbers do not cross-contaminate. If Dmitri refreshes or the polling fires, the counts do not change.

**Concern:**

Frontend might cache the yesterday response incorrectly, mixing it with today's data. The backend query might return sessions from both days when filtering on a single date. The 10-second polling cycle might clobber the yesterday view's data every 10 seconds, forcing Dmitri to watch it flicker.

**Property:**

For any date D, all returned sessions have completed_at in the range [D 00:00 UTC, D 23:59:59 UTC). Querying D and D-1 returns disjoint session sets.
