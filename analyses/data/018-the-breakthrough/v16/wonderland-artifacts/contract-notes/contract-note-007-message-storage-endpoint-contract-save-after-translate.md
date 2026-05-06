## Contract Note 007: Message storage endpoint contract (save-after-translate)

**State:** agreed
**Contract Version:** v1 (POST /api/messages with optional translated_text; idempotent 5s window)

**Current Shape:**

No explicit contract yet.

**Proposed Change:**

Backend exposes endpoint POST /api/messages. Request body: { original_text (string), original_language (enum), translated_text (string, nullable), target_language (enum, nullable), message_retention_flag (string) }. Response: { message_id (UUID), sender_id (UUID), original_text (string), original_language (enum), translated_text (string, nullable), target_language (enum, nullable), translation_status (enum: complete | pending | failed), translation_timestamp (timestamp, nullable), translation_model (string, nullable), created_at (timestamp) }. 

Semantics:
- If translated_text is provided (non-null), backend sets translation_status=complete + translation_timestamp=now().
- If translated_text is null, translation_status=pending (translation will be completed asynchronously).
- Idempotence: if caller POSTs same (original_text, original_language, target_language) within 5-second window, backend deduplicates and returns existing message_id instead of creating duplicate. After 5s, treated as new message.

**Source:** adr#1 and ticket#1: message storage must persist immediately (Maria/James stories expect reliability); translation is optional at storage time (handles case where translation is still in flight or failed).

**Frontend Impact (Tweedledee):**

Frontend workflow:
1. User sends message with (original_text, original_language, target_language).
2. Frontend calls POST /api/translate to get translation.
3. On translate success: Frontend calls POST /api/messages with translated_text populated and translation_status will be set to complete by backend.
4. On translate failure: Frontend calls POST /api/messages with translated_text=null; backend sets translation_status=pending. User sees message stored with 'retry' button.
5. Response includes message_id, which frontend stores and uses for subsequent display/edit operations.

**Backend Impact (Tweedledum):**

Backend implements POST /api/messages. Receives: { original_text, original_language, translated_text (nullable), target_language (nullable), message_retention_flag }. 

Validation:
- original_text: non-empty, ≤2000 chars
- original_language, target_language: valid enum values
- message_retention_flag: set per Sophie's GDPR story; backend enforces retention policy

Processing:
- Generates message_id (UUID)
- Writes message record immediately with all provided fields
- If translated_text is provided (non-null): sets translation_status=complete, translation_timestamp=now(), translation_model='claude-haiku-4.5'
- If translated_text is null: sets translation_status=pending, translation_timestamp=null
- Returns full message record in response

Idempotence: If POST arrives with same (original_text, original_language, target_language) within 5-second dedup window, backend checks existing messages table. If found, returns existing message_id and current record state. After 5s, no dedup—treated as new message.

Immutability: original_text and original_language are immutable after creation. Only translated_text, translation_status, translation_timestamp can be updated (via PUT endpoint; see contract 009 if needed).

**Resolution:**

Agreed. Message storage contract locked. Frontend controls save timing (after translate completes); backend enforces invariants (original immutable, translation_status=complete ⟹ translated_text non-null). Dedup window 5s.
