## Contract Note 001: Translation Status Signal Shape

**State:** agreed
**Contract Version:** translation-status-signal v1 (message-envelope extension: translation_status enum + translated_body field + source_language + target_language)

**Current Shape:**

Not yet specified. Assuming message envelope includes a translation_status field, but the enum and the timing of status transitions are open.

**Proposed Change:**

The frontend needs to track four states: (1) message received, original language only (loading state from user POV); (2) translation in flight (pending-sync); (3) translation arrived (translated + timestamp); (4) translation SLA missed, recoverable error (error-recoverable — show original + 'translation unavailable, retry?' CTA). The contract should name these states explicitly and specify whether the backend sends status-update events (WebSocket) or whether the frontend polls, or hybrid.

**Source:** Cat's ADR routing 2s SLA with graceful degradation — frontend needs to know when we're past the SLA window so we can show the right UI.

**Frontend Impact (Tweedledee):**

If status updates come via WebSocket events, we hold translation_status in client state (message ID -> {status, timestamp, translated_body}). Reconciliation rule: canonical source is the server; client state is read-ahead cache for display. If the connection drops mid-translation, we fall back to the original + error state and re-request on reconnect. If we poll instead, we add a client-side timer per message that fires at 2.1s and shows error state if translation hasn't arrived. WebSocket is preferred (cleaner state, fewer timer leaks); polling is acceptable if that's easier on the backend.

**Backend Impact (Tweedledum):**

Backend can emit translation-status events reliably for three states: (1) received, not-yet-requested; (2) in-flight; (3) complete. The fourth state — SLA miss after 2s — requires frontend contract clarity: does `translation_timeout` event mean "gracefully show original" or "show error, allow retry"? Also: do we cache translation results on backend (affects GDPR surface, simplifies repeated reads) or fresh-translate every read (higher translator throughput cost, guaranteed fresh)? This is a cost/surface tradeoff decision that shapes the service topology.

**Resolution:**

Tweedledum confirms backend delivery constraints and cache lifetime expectations. Frontend then implements per the four UI states. Contract version locks once both sides confirm the signal shape is complete.
