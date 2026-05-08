## Ticket 004: Log completed sessions to persistent history

**Sources:** daily-review-of-session-history
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 55% confident
**Status:** open

**Dependencies:**
- Blocks: daily-review-of-session-history
- Blocked by: persistent-settings-across-app-launches
- Soft: —

**Description:**

When a focus or break session completes (timer reaches 0), record: start time, end time, session type (focus/break), duration configured, duration actual, user action (completed or skipped). Store in persistent backend or local DB. Design the schema to support later queries by day/week.

**Acceptance:**
- Session completion is logged with full metadata
- Logs are persisted and survive app restart
- Logs can be queried by date (necessary for daily review)
- Schema allows distinguishing completed sessions from skipped sessions

**Risk:**

Unclear whether logs live in localStorage or a backend service — this is an architectural choice the Cat should have covered in the ADR. If the ADR is silent, this ticket may need to block for a contract negotiation between Tweedles.
