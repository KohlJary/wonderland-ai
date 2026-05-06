## Contract Note 001: Message envelope: original and translated text with metadata

**State:** agreed
**Contract Version:** message-envelope-v1 (original_text + translated_text + translation_status enum + source/target language FKs)

**Current Shape:**

Messages carry text, sender_id, timestamp, conversation_id. No translation metadata.

**Proposed Change:**

Add original_text, translated_text, translation_provider, source_language, target_language, translation_status (enum: pending, completed, failed, not_requested). Versioning via envelope_schema_version field (currently 1).

**Source:** ticket-001 (message contract: translation metadata), ADR-001 hub-model, story sources: monolingual-user-sends-message-across-language-boundary, user-receives-translated-message-and-wants-to-see-the-original

**Frontend Impact (Tweedledee):**

Message display component binds to translated_text by default, with a toggle to original_text. Requires both fields populated or explicitly null (not omitted) — my component guards against missing keys, not against null values that mean 'no translation happened'. Indexing strategy: I'll query by conversation_id + translation_status; single composite query is cleaner for UI pagination. Language labels rendered from source_language and target_language enums. UI states: message-loading (pending), message-error (failed), message-with-toggle (translated text + original accessible), message-monolingual (translated_text == original_text, toggle hidden). Can you clarify the 'failed' case? If translation_status is 'failed', do I show the original_text with an error badge, or do I hide the message entirely?

**Backend Impact (Tweedledum):**

Message creation now requires translation metadata fields. DB schema extends message table with new columns (original_text nullable, translated_text nullable, translation_status enum, source_language FK, target_language FK, translation_provider string). Backward-compatible migration: existing messages get envelope_schema_version=0; new messages v1. Transactional boundary: message and its metadata are atomic — either both exist or neither.

Invariant: a message has exactly one source language and one target language, and if translation_status is 'completed', both translated_text and original_text are present. If translation_status is 'failed', translated_text is null and original_text is present. If translation_status is 'pending', translated_text is null, original_text present, and the message is in flight to the translator.

Query impact: UI will likely query by conversation_id and filter by translation_status (show translated, show original, show both). Need to discuss indexing strategy — should these be individual queries or single composite?

**Resolution:**

Backend enforces invariants: (1) if translation_status='completed', both original and translated non-null and differ; (2) if 'failed', original non-null, translated null; (3) if 'pending', waiting in flight; (4) if 'not_requested', message not sent at all. Your question on 'failed' case: show original with error badge, not hidden. Composite index (conversation_id, translation_status) supports your pagination. Migration backward-compatible.
