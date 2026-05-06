## Contract Note 004: Translation failure visibility and error propagation

**State:** agreed
**Contract Version:** error-handling v1 (translation_failed status with error_code + error_message; frontend shows original with error notice)

**Current Shape:**

Skeleton has no error handling for failed translations.

**Proposed Change:**

When a message has translation_status = translation_failed, the frontend renders the original_text with an error notice ('Translation failed for this message; showing original'). The error_code and error_message fields are populated from the translation service's response (e.g., error_code='500', error_message='service unavailable'). Frontend may optionally show the error_code to the user for debugging ('error: 500') or log it silently; UX decision is yours. The user can optionally request a retry (future ticket), but v1 does not support retry UI. Message is readable, just not translated.

**Source:** ADR-002 error visibility; ticket-004 risk mitigation; compliance with 'show original on failure' semantics.

**Frontend Impact (Tweedledee):**

When translation_status=translation_failed, frontend renders original_text with error notice: 'Translation failed for this message; showing original.' Error code and error message are available in the response; frontend may log them silently or show error code to user (UX TBD, no user-facing error detail in v1). No retry UI in v1. Message is readable to user, just not translated. This satisfies graceful degradation: user sees useful content (the original) rather than a failed state.

**Backend Impact (Tweedledum):**

When translation service returns an error, backend writes translation_status = translation_failed, populates error_code and error_message from the service response, and logs the event. Translated_text remains null. The message is persisted and visible immediately to the frontend (with failed status), so user sees 'this didn't translate, here's the original' without waiting for a retry or admin action. This is the 'graceful degradation' mode.

**Resolution:**

AGREED. Contract-note-004 (Tweedledum's backend error handling) and Tweedledee's response on frontend error display describe the same graceful-degradation contract. When translation service fails, backend sets translation_status=translation_failed, populates error_code and error_message from service response, logs the event, and persists the message (translated_text remains null). Frontend renders original_text with error notice ('Translation failed for this message; showing original'). Message is readable; user sees the original rather than an error state. Canonical reference: contract-note-004.
