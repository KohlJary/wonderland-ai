## Ticket 001: Define session state machine and contract for Timer ↔ History seam

**Sources:** story:start-and-complete-a-focus-session, story:take-and-track-a-break, adr:separate-timer-history-and-settings-into-distinct-persistence-entities
**Owner:** tweedledee, tweedledum (pair contract negotiation)
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:schema-and-migrations-for-timer-and-history, ticket:timer-state-machine-and-session-lifecycle, ticket:history-append-only-log-and-session-aggregation
- Blocked by: —
- Soft: —

**Description:**

Before either Tweedle ships Timer or History, nail the contract: what fields does a completed session carry? What guarantees does Timer give History about write atomicity? Does History consume events or does Timer write directly? Document this as an explicit contract note — it's the load-bearing seam.

**Acceptance:**
- Contract document names Timer fields (session_id, duration, type, start, end, completed_at, etc.)
- Contract specifies write atomicity: Timer and History writes happen in same transaction or Timer emits event that History consumes?
- Contract names the seam: where Timer hands off to History
- Both Tweedles have signed off; document lives in repo

**Risk:**

If Tweedles disagree on event vs. transaction pattern, this blocks both Timer and History. Resolve early with the Cat's input if needed — she may have architectural preference based on crash-safety.
