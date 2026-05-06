## Contract Note 005: Message envelope: shape of POST /conversations/{id}/messages response

**State:** agreed
**Contract Version:** v1 (message envelope: { id, conversation_id, sender_id, sender_display_name, original_text, original_language, translated_text, translated_language, created_at })

**Current Shape:**

No message endpoint yet; placeholder HelloMessage returns {id, text, created_at}.

**Proposed Change:**

POST /conversations/{id}/messages (sender creates a message). Response should include: id, conversation_id, sender_id, sender_display_name, original_text, original_language, translated_text, translated_language, created_at. Question: does frontend need both original_language and translated_language, or can it infer translated_language from recipient's preference (passed separately)? Does frontend display the translation immediately, or does it show loading state during API call?

**Source:** ticket/create-messages-and-conversations-schema-add-send-message-endpoint and story/english-speaker-initiates-a-chat-with-a-german-speaker

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

Backend calls translation API (TBD: Claude, Google Translate, etc.) synchronously. If translation is slow (>2s), this blocks the response. For MVP, sync acceptable. Response includes both original and translated text, both language tags. Error case: translation fails; backend returns 500 or does it retry with fallback?

**Resolution:**

Agreed. Backend infers original_language from sender's language_preference, translated_language from recipient's language_preference. Translation happens synchronously (request blocks). If translation fails, return 500. Frontend displays both original and translated text per Alice's story. Optimistic display: message appears immediately with loading spinner; translation resolved when API returns.
