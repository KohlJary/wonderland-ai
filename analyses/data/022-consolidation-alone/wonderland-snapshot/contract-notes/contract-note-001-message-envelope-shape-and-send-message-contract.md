## Contract Note 001: Message envelope shape and send-message contract

**State:** agreed
**Contract Version:** v1

**Current Shape:**

No contract yet; placeholder /api/messages echo only

**Proposed Change:**

POST /conversations/{conversation_id}/messages endpoint. Request envelope: { original_text: string }. Response envelope: { id, conversation_id, sender_id, sender_display_name, original_text, original_language, translated_text, translated_language, created_at }. Request headers: HTTP Basic auth (email:password). Frontend assumption: original_language is inferred server-side from sender's language_preference (not sent); translated_language is inferred from recipient's language_preference (not sent); translation happens synchronously (request blocks until translation API returns); if translation fails, 500; if auth fails, 401; if sender not in conversation, 403.

**Source:** ticket/create-messages-and-conversations-schema-add-send-message-endpoint + alice story/english-speaker-initiates-a-chat-with-a-german-speaker

**Frontend Impact (Tweedledee):**

Frontend sends POST /conversations/{conversation_id}/messages with { original_text }. Backend returns message object with both original and translated text + both language tags. Frontend parses response and displays both languages per Alice's story (Story 002: user sees 'original text, translated text'). Frontend will show optimistic display (message appears immediately in list with loading spinner on translation; translatio resolved when API response arrives). Auth header required on every request; frontend stores email+password in memory and base64-encodes into Authorization: Basic header.

**Backend Impact (Tweedledum):**

POST /conversations/{conversation_id}/messages request: { original_text: string }. Response: { id, conversation_id, sender_id, sender_display_name, original_text, original_language (inferred from sender's language_preference), translated_text, translated_language (inferred from recipient's language_preference), created_at }. Backend calls translation API synchronously; if translation fails (timeout / API error), return 500 with error detail. Auth via HTTP Basic header (email:password base64-encoded); validated on every request. Invariants: message has exactly one sender, one recipient, both in the same conversation; original_language and translated_language are always populated; created_at is server-generated. Schema: messages table with (id, conversation_id, sender_id, recipient_id, original_text, original_language, translated_text, translated_language, created_at). Sender and recipient inferred from conversation context (sender = authenticated user, recipient = the other user in the conversation).

**Resolution:** Agreed v1. Frontend receives and displays both original and translated text with language tags. Languages inferred server-side. Translation is synchronous (blocks response).

---

**History:**

- **2024-01-XX (Tweedledee propose):** Initial proposal with frontend expectations and backend fill-ins left pending.
- **2024-01-XX (Tweedledum propose as note-005 in parallel):** Proposed same seam, raised clarifying questions.
- **2024-01-XX (Tweedledee consolidate and mark agreed):** Consolidated to one-per-seam; confirmed frontend needs both language tags; marked agreed pending backend confirmation.
