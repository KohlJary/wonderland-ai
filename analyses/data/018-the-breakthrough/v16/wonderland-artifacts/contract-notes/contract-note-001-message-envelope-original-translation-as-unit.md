## Contract Note 001: Message envelope: original + translation as unit

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Current message record has text, language_code, timestamp, sender_id. No translation field.

**Proposed Change:**

Add to message record: original_text, original_language, translated_text, target_language, translation_model, translation_timestamp, translation_status ('pending' | 'success' | 'failed'), translation_error (nullable). Keep existing text field as backward-compat; new clients read original_text. For v1, support 1:1 language pair (one message = one source language, one target language). Multi-target is fast-follow.

**Source:** ticket-001, adr-001: translation-as-unit-level-transformation. Storage schema decision blocks both service (ticket-002) and UI (ticket-003).

**Frontend Impact (Tweedledee):**

UI must handle all four translation_status values: pending (show spinner or 'translating...'), success (show both original and translation), failed (show original only + error message + 'retry' button). Client state: toggle preference (show_original: boolean) lives on client, persisted per-session but not to disk in v1. Message record from server is the source of truth for translation_status; client does not predict or infer status.

**Backend Impact (Tweedledum):**

Backend accepts (original_text, original_language, target_language) from frontend. Backend writes message record with original_text + original_language + message_retention_flag immediately (timestamp T0). Backend calls translation service asynchronously or synchronously (TBD in translation-service contract note). On translation completion, backend updates translated_text + translation_timestamp + translation_status=complete. On translation failure, translation_status=failed (message visible in UI with 'translation failed' indicator; retry available). GDPR compliance: message_retention_flag set per Alice's stories (Sophie's story surfaces GDPR scope); deletion of message cascades to translation record—no orphaned translations. Query load: frontend requests message by message_id (includes original + translation). No translation-status filtering on backend—UI handles 'translation pending' display. Invariant: (translation_status = complete) ⟺ (translated_text is non-null AND translation_timestamp is non-null). Invariant: message_id is globally unique and immutable.
