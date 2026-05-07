## Contract Note 002: Session Complete Request/Response Shape

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

(none yet — first draft)

**Proposed Change:**

POST /sessions/{id}/complete — request is empty; response is {id, session_id, start_time, end_time, duration_seconds, is_completed}. Backend transitions state to completed, sets end_time to server-provided now(), marks is_completed=true, persists.

**Source:** story-001 (start-and-complete-a-focus-session) + ticket-003 (frontend-session-complete-button)

**Frontend Impact (Tweedledee):**

Frontend detects timer expiry (target_duration_seconds elapsed) or user taps "Complete" button. POSTs to /sessions/{id}/complete with empty request body. On 200 response with {id, end_time, duration_seconds, is_completed=true}, transitions UI to "session-complete" state. Displays duration_seconds as the authoritative session length (not computed client-side). Client state: clears active session, moves session record to completed list. Optimistic update: client assumes success immediately (shows completion UI) while POST is in flight; if POST fails (500, network error), rolls back to "timer-running" state and shows error-recoverable message "Couldn't complete session. Try again?" No retry logic on 409 or 403 — those are permission/state errors, not transient failures.

**Backend Impact (Tweedledum):**

Only transitions active→completed if is_active=true. If already completed, returns 409 'session already completed' (idempotent — can resend safely). If not found or not owned by user, returns 403. Computes duration_seconds = end_time - start_time. Never allows backdating: end_time is always server-provided now(), never client-provided (prevents clock-drift abuse). Failure modes: if the persist fails after state is computed in memory, return 500 with instruction to retry; client-side optimistic update is valid but not guaranteed.

---

**Open questions for pair:** 

1. On 409 idempotent response (already completed): should we return the original end_time + duration_seconds so frontend can verify it matches what was sent? Or just 409 with no body? Frontend impact: if we return the record, frontend can confirm it's the same session and not show an error.

2. On 500 retry: does backend want us to backoff + retry up to N times? Or should frontend show error immediately and let user retry manually?
