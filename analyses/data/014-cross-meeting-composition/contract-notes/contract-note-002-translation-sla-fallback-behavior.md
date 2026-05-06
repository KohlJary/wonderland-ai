## Contract Note 002: Translation SLA Fallback Behavior

**State:** agreed
**Contract Version:** v1 (translation_failed event with failure_reason enum: timeout | service_error | network_error)

**Current Shape:**

Message arrives, frontend displays original, translation fetch happens asynchronously within 2-second window per Cat's proposal.

**Proposed Change:**

Explicit contract signal for when translator misses SLA: either (A) return original untranslated with a specific enum value in the message-status field, or (B) return 'translation-pending' state that frontend polls/waits for. If (B), we need a hard timeout the client enforces independently.

**Source:** Tweedledum's concern: the Cat's SLA assumption doesn't specify fallback; the frontend's ability to show the correct UI state depends on knowing which fallback behavior the backend chose.

**Frontend Impact (Tweedledee):**

The frontend must distinguish between 'translation timed out after 2s' and 'message failed to send.' For timeout, show original language with retry affordance. For send failure, show error state. The contract signal must distinguish these cases. The timeout is not an error from the user's perspective — it's graceful degradation. If Tweedledum's backend can emit `translation_timeout` as a distinct event (not bundled with a generic error), the frontend can render appropriately.

**Backend Impact (Tweedledum):**

Backend emits `translation_timeout` event after 2s if translator doesn't respond. Separate `translation_failed` event with `failure_reason` enum (`timeout`, `service_error`, `network_error`) so frontend can differentiate error handling. Requires explicit timeout handling in the translation service and event-emission logic.

**Resolution:**

agreed—backend emits translation_failed with reason enum, frontend interprets and renders accordingly
