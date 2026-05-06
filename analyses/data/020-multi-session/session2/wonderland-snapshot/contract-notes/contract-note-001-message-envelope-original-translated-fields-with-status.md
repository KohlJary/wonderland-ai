## Contract Note 001: Message envelope: original + translated fields with status

**State:** agreed
**Contract Version:** message-envelope v1 (sender sees original_text, receiver sees translated_text with attribution; both fields always present; translation_status enum; error_code/error_message on failure)

**Current Shape:**

Skeleton has a placeholder Message model. Real contract needs: what fields the API returns, which are required vs. nullable, how language info is encoded.

**Proposed Change:**

GET /conversations/{conversation_id}/messages returns array of message objects: { message_id, sender_id, original_text, translated_text, language_pair (string: 'de-en'), translation_status (enum: pending_translation | translated | translation_failed), created_at (ISO8601), translated_at (ISO8601 or null if pending), error_code (string or null), error_message (string or null) }. Both original_text and translated_text are always present in the response (original is always populated at send; translated is null until status = translated). Language_pair is immutable (set at message creation from sender and receiver language preferences).

**Source:** ADR-002 dual-language display contract; ticket-003 acceptance criteria.

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

API endpoint must query Message table, join to Conversation to get language_pair info (or store language_pair on Message itself for denormalization), check membership (caller must be one of the two users), and return all fields. Response latency target <100ms. No translation work here — just data retrieval and visibility. Membership check prevents non-participants from reading. Schema change: Message table must have all these fields with appropriate nullability (translated_text nullable, error_code nullable, error_message nullable). All fields are indexed or cached appropriately.

**Resolution:**

AGREED. Contract-note-005 (Tweedledee's perspective) and contract-note-001 (Tweedledum's perspective) describe the identical schema and rendering asymmetry. The backend message-envelope contract is locked: Message(id, conversation_id, sender_id, original_text, translated_text, language_pair, translation_status, created_at, translated_at, error_code, error_message). API response includes all fields; membership check prevents non-participants. Both texts always present in response; translated_text nullable at DB layer but always included in response shape (null or empty-string). Canonical reference: contract-note-005 for frontend rendering logic + contract-note-001 for backend schema.
