## Contract Note 001: Session persistence and state model

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No persistent contract yet; currently timer is ephemeral.

**Proposed Change:**

Define where session lifecycle data lives and how it flows. Specifically: (1) Is there a backend service, or is all state local (localStorage)? (2) If local, what's the schema for a session record? (3) When does a session get created/updated/deleted?

**Source:** Ticket-003 (persist settings) and Ticket-004 (log sessions) both need clarity on where state lives. Ticket risk notes indicate this is an architectural gap.

**Frontend Impact (Tweedledee):**

Frontend creates sessions via POST /sessions/log (contract-note 005). Timer runs locally; no offline-first semantics for v1 — network failure = retry loop with exponential backoff. Sessions are backend-canonical; frontend has no local session store. This means: (1) I drive timer locally and emit exactly once when timer reaches configured duration. (2) No session object on client except ephemeral (current timer state). (3) Network loss mid-session: frontend queues the completion event and retries until acknowledged. Does this shape match your persistence model?

**Backend Impact (Tweedledum):**

If sessions live in localStorage only, I need to define a local schema: { id, type ('focus'|'break'), startTime, endTime, durationConfigured, durationActual, status ('running'|'paused'|'completed'|'skipped') }. I'll also need to handle migrations if the schema evolves. If sessions live in a backend service, I'll need to design endpoints for create/update/query, define retry/conflict semantics, handle offline mode.
