## Contract Note 005: Message Envelope: dual-language display with translation status

**State:** agreed
**Contract Version:** message-envelope v1 (sender_id, original_text, translated_text, language_pair, translation_status, created_at, translated_at, error_code, error_message)

**Current Shape:**

Skeleton returns Message(sender_id, text, timestamp). Does not distinguish original from translation.

**Proposed Change:**

API returns Message(sender_id, original_text, translated_text, language_pair, translation_status, created_at, translated_at, error_code). Both original and translation always present (never null, but translated_text is empty string while translation_status=pending_translation). language_pair is source→target (e.g., 'de→en'). translation_status is enum: pending_translation | translated | translation_failed.

**Source:** adr-002 (dual-language display); ticket-003 (API spec); story-001, 002 (Yuki needs both versions; Klaus needs transparency that this is a translation)

**Frontend Impact (Tweedledee):**

Frontend renders differently based on whether caller is sender or receiver. Sender always sees original_text in sender's language. Receiver sees translated_text (when available) with attribution label 'Original: [original_text] (translated from [source_lang])'. While translation_status=pending_translation, show 'translating...' indicator and original_text. While translation_status=translation_failed, show original_text with error notice. This contract's fidelity requirement (both texts visible, labeled) is non-negotiable for story-001 and story-002 personas.

**Backend Impact (Tweedledum):**

Message table schema: (id, conversation_id, sender_id, original_text, translated_text, language_pair, translation_status, created_at, translated_at, error_code, error_message). All fields except id, conversation_id, sender_id, created_at are included in every API response. Nullability: translated_text and translated_at are null while translation_status=pending_translation; error_code/error_message null until status=translation_failed. Index on (conversation_id) for fast list queries. Response includes all messages in conversation (no pagination for v1, assuming <10k messages per conversation). API membership check: query conversation, verify caller is one of the two users, return 403 if not. Frontend Impact (Tweedledee): your proposed rendering logic (sender sees original, receiver sees translation with attribution) is exactly what the contract supports. AGREED.

**Resolution:**

Frontend rendering (sender sees original, receiver sees translation with attribution) is supported by backend schema (both texts returned, nullability rules, membership check, indexing). API contract is locked.
