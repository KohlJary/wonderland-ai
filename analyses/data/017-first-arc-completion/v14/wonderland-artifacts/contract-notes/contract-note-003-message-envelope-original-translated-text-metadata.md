## Contract Note 003: Message envelope: original + translated text + metadata

**State:** agreed
**Contract Version:** v1 (same as 001, clarified: translation_status owns the contract; if 'not_requested', message doesn't exist at all; if 'failed', only original_text present; if 'completed', both present and differ)

**Current Shape:**

Messages currently carry only translated text. No source-language tracking, no original-text field.

**Proposed Change:**

Extend message envelope to: { id, text, created_at, author_id, translated_text, original_text, source_language, target_language, translation_provider, schema_version }. Both original_text and translated_text are always present; if no translation occurred (consent missing, languages match, translation failed), original_text == translated_text and translated_text is null or both are the same. Alternatively: one is the primary text, the other is optional. Design choice: should I (frontend) always expect both fields populated, or should I handle the 'single text' case?

**Source:** Ticket 001 (message contract), Stories 1 and 3 (cross-language message flow, original-text toggle)

**Frontend Impact (Tweedledee):**

I will build a message display component that binds to translated_text by default and shows a toggle to switch to original_text if both are present and differ. The component needs language labels: 'Original: [source_language]', 'Translated: [target_language]'. If the envelope doesn't reliably carry both fields, my component logic becomes fragile (null-checks, type guards, fallback copy). I need a clear contract: when does each field exist, and what does null mean?

**Backend Impact (Tweedledum):**

Message envelope must carry both original_text and translated_text as persistent fields in the message table. Backend guarantee: (1) if translation_status = 'completed', both fields are non-null and differ; (2) if translation_status = 'failed', original_text is non-null, translated_text is null; (3) if translation_status = 'pending', original_text is non-null, translated_text is null, and the message waits in the 'pending' state until translation completes or fails (timeout: 30 seconds, then status = 'failed'). (4) if translation_status = 'not_requested' (source_language == target_language or consent not given), both fields are null and the message should not be sent at all — the frontend should not render it. Invariant: a message has exactly one source_language and one target_language; both must reference the languages table. Indexing: composite index on (conversation_id, created_at) for list queries; separate index on translation_status for filtering. Your question about 'single text case': that is the 'not_requested' status — there is no message at all if translation was not requested. If translation succeeded, both fields exist. If it failed, only original exists. The contract is: the envelope always carries both fields' *existence* status, never ambiguous null-checks on the frontend. You always know what you're rendering.

**Resolution:**

Agreed. Status enum is the contract. Eliminates 'single text case' ambiguity. I expect both fields' existence to be determined by translation_status. Backend guarantee: status tells the story, no gaps.
