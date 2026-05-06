## Contract Note 003: Error Recovery and Retry Behavior

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

On translation_status={failed, timeout}, backend returns failure_reason enum {timeout, service_error, network_error}. Frontend behavior on error: unspecified.

**Proposed Change:**

Formalize error recovery: (1) Retry is client-initiated only. User sees 'Translation unavailable — original message shown' and can tap 'retry translation' button. (2) Retry re-requests the translation for the same message_id, source_lang, target_lang. (3) failure_reason is cached by frontend for observability telemetry but never shown to user. (4) No server-side auto-retry, no message state tracking.

**Source:** Frontend UX design + backend statefulness constraint. Backend translation handler is stateless-per-request; if server auto-retry were needed, it would require message state management (queuing, retry backoff, etc.). Client-initiated retry keeps that out of scope.

**Frontend Impact (Tweedledee):**

Frontend maintains simple UI states: loading (awaiting translation), translated (translation_status=translated, translated_text displayed), error-recoverable (translation_status=failed/timeout, original displayed, 'retry' button shown). No state tracking across retries; each retry is independent.

**Backend Impact (Tweedledum):** _pending_
