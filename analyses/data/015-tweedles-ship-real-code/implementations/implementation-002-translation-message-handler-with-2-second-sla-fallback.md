## Implementation 002: Translation message handler with 2-second SLA fallback

**Side:** backend
**Ticket:** translation-mvp-001
**Contract:** Translation Status Signal Shape v1 (status enum {pending, translated, failed, timeout}), Translation SLA Fallback Behavior v1 (failure_reason enum {timeout, service_error, network_error}), WebSocket Statefulness v1 (stateless requests with message_id, source_lang, target_lang)
**Ready for review:** yes

**Approach:**

Stateless async handler wrapping a stub translator call. Enforces 2-second SLA using asyncio.wait_for(). Returns TranslationResponse dict with status enum (pending, translated, failed, timeout) + translated_text (on success) or failure_reason (on failure). Handles timeout, service_error, network_error cases with explicit exception mapping.

**Invariants Enforced:**
- Every call returns a response dict with message_id and status (enforced by return type)
- status is one of {pending, translated, failed, timeout} (enforced by TranslationStatus enum)
- If status == 'translated', translated_text is a non-null string (enforced by success path)
- If status == 'failed' or 'timeout', failure_reason is set (enforced by exception handlers)
- translated_text and failure_reason are mutually exclusive (enforced by TypedDict + conditional logic)

**Schema Changes:**

No database migrations; response envelope is transient (not persisted). Message-translation endpoint input/output shape locked to contract v1.

**Failure Modes Handled:**
- Timeout (translator takes >2s): return status=timeout, failure_reason=timeout via asyncio.TimeoutError catch
- Service error (translator service error): return status=failed, failure_reason=service_error via TranslationServiceError catch
- Network error (translator network failure): return status=failed, failure_reason=network_error via TranslationNetworkError catch
- Unexpected exception: return status=failed, failure_reason=service_error as safe default

**Files:**
- src/translation_handler.py: Translation handler with async handle_translation_request() function, TranslationStatus and FailureReason enums, TranslationResponse TypedDict, and _stub_translator() with 50ms notional delay

**Open Questions for Pair:**
- Does Tweedledee want the message-translated WebSocket event to include the full TranslationResponse, or only status + translated_text with message_id as the key?
- Should the frontend cache the translated_text from the event payload, or treat the event as a signal to re-request authoritative state?
- For failure_reason enum values (timeout, service_error, network_error), should these map to user-facing error strings, or is that frontend's responsibility?

**Known Limitations:**
- Stub translator returns hardcoded format; no real translation service integration (deferred to v2)
- No observability instrumentation yet (Dormouse will add metrics/tracing in v2)
- Exception handling defaults to service_error for unexpected failures (production should log + alert)
