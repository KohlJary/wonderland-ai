## Ticket 005: Implement break timer backend and state management

**Sources:** take-a-break-and-prepare-for-the-next-session
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: session-history-query
- Blocked by: session-timer-backend
- Soft: —

**Description:**

Build the backend break timer: track break start time, elapsed time, and state. Store break records in the database. Expose an API endpoint for break status. When a break completes, mark it complete in the database. This is mirrored to the session timer backend—same patterns, same reliability requirements.

**Acceptance:**
- Break can be created with a configurable duration
- Break state transitions are tracked
- API endpoint returns current break elapsed and remaining time
- Break record is persisted with timestamps
- User can skip a break and transition directly to a new session without data loss

**Risk:**

State transition complexity if a skip happens during break completion; add idempotent checks.
