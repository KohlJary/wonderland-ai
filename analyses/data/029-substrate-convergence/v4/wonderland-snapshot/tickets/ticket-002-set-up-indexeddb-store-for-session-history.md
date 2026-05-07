## Ticket 002: Set up IndexedDB store for session history

**Sources:** view-and-understand-local-first-persistence
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: session-history-persistence, session-ui-rendering
- Blocked by: session-record-schema
- Soft: —

**Description:**

Implement IndexedDB schema and basic CRUD (create, read, list, update) for session records. Do not implement UI yet; this is the persistence layer. Include: schema versioning approach (how do we handle IndexedDB schema upgrades if v1 ships and we later change the record shape), transaction handling for multi-record operations, error handling for quota exceeded.

**Acceptance:**
- IndexedDB store initialized on app load
- Can create a session record and retrieve it
- Can list all sessions for a given day
- Handles quota-exceeded error gracefully
- Schema version strategy documented

**Risk:**

IndexedDB quota behavior differs across browsers; may need fallback strategy (localStorage for small datasets, or graceful degradation). Expand to 2 days if quota handling is complex.
