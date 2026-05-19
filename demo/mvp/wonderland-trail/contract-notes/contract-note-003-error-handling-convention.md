# Contract Note: Error handling convention and recovery semantics

**GUID:** 01KRXXAC-tweedle-substrate-thread-003
**State:** proposed
**Contract Version:** (unlocked)

## Current Shape

n/a — fresh feature thread for substrate v1

## Proposed Change

POST/PATCH error responses use HTTP convention:

- **4xx (Validation/Client Error):** title missing, body too long, tag_id invalid, duplicate tag_ids, etc.
- **5xx (Server Error):** database failure, service unavailable, permission denied, etc.

Error response shape (both 4xx and 5xx):
```json
{
  "error": "ValidationError | ServerError | AuthorizationError",
  "detail": "string (human-readable description)",
  "field": "string (optional, which field had the error)"
}
```

## Recovery Semantics

Client treats both 4xx and 5xx as retryable:
- Preserve localStorage (user's draft survives)
- Show error text to user in error-recoverable UI state
- Keep Save button clickable for manual retry
- Network timeout (no response) is treated as 5xx

Clear localStorage only on 200 response.

## Source

Tweedledum's question 3: "Should I use HTTP status codes (5xx vs 4xx) to signal retryable vs terminal failures?"

Ticket-001KRXRVT (Save failure and recovery)
User need: Kohl's keystrokes must survive failures and be available for retry or recovery.

## Frontend Impact (Tweedledee)

Error handling:
- Both 4xx and 5xx: preserve localStorage, show error message, allow manual retry
- Network timeout: same as 5xx (assumed transient, show error, allow retry)
- Component state: {isSaving: false, error: <error detail>} after failure; Save button re-enabled

No automatic retry or exponential backoff in v1 (manual retry via Save button).

## Backend Impact (Tweedledum)

Use HTTP convention for error classification. Both 4xx and 5xx are treated as recoverable from the client's standpoint (localStorage preserves the user's work).

In v2+, if automatic retry + idempotency becomes necessary, we can add request ID headers and idempotency semantics; the basic error handling contract doesn't change.

## Resolution

Proposed — awaiting your confirmation that the error shape and status code semantics match your implementation.
