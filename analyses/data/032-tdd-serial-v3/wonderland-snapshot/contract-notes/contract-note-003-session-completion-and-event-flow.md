## Contract Note 003: Session completion and event flow

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None. Timer counts down; when it hits 0, the UI emits an event (implicitly).

**Proposed Change:**

Define the event contract for session completion. When a session ends (timer reaches 0), what happens? (1) Does the frontend emit an event ('sessionEnded') that the backend listens to? (2) Or does the frontend call an endpoint (POST /sessions/{id}/complete)? (3) What data is included in the completion event/payload?

**Source:** Story-001 (Marcus) needs clear signal when session ends. Ticket-006 (audio) plays on completion. Ticket-004 (history logging) needs to capture when sessions end. These all depend on a well-defined completion event.

**Frontend Impact (Tweedledee):**

Contract-note 005 specifies this: frontend POSTs /sessions/log when timer reaches 0. No user acknowledgment needed — completion is implicit. App backgrounding doesn't block the event; completion fires client-side regardless. If app is backgrounded and restarted, POST still fires (it was queued locally). The event envelope is { type, duration_configured_seconds, duration_actual_seconds, completed_at }. Idempotency: I'll retry with exponential backoff; backend should treat the (session_id or timestamp) as idempotent key. Does the event shape work, or do you need additional fields for analytics/aggregation?

**Backend Impact (Tweedledum):**

If event-driven: I listen for a 'sessionCompleted' event with { sessionId, actualDuration, completedAt }. I persist it and update aggregates (daily totals). If REST: I expose a POST endpoint that accepts the completion payload and returns confirmation. I also need to handle: what if the event fires twice (idempotency)? What if the session was actually paused, not completed?
