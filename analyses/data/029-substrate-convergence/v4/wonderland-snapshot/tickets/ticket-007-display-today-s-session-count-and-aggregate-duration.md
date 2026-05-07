## Ticket 007: Display today's session count and aggregate duration

**Sources:** review-today-s-session-count
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: session-persistence
- Soft: session-history-daily-view

**Description:**

Below the timer or in a summary section, show: total sessions completed today, total focused time today. Recompute whenever a session completes. Simple query: count records with start_time in today's date, sum their durations.

**Acceptance:**
- Count of today's sessions is displayed
- Total duration is computed and shown
- Updates immediately when a session completes

**Risk:**

None; low complexity.
