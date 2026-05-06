## Contract Note 004: Message GET response envelope (message-envelope-get-v1)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

not yet defined

**Proposed Change:**

GET /conversations/{conversation_id}/messages?read_language={lang_code} returns array of message objects. Each message is: {id: string, sender_id: string, sender_name: string, text_original: string, text_language: string, text_translated: string, created_at: timestamp, translation_status: enum('success' | 'pending' | 'error'), translation_error?: string}. Sender sees their own messages with text_original populated and text_translated empty (or same as original). Receiver sees both text_original and text_translated populated. translation_error is present only if translation failed (e.g., vendor timeout); frontend shows warning to user.

**Source:** ticket 005 (message-send-and-receive-api-endpoints) acceptance criteria: 'Response includes metadata for frontend (sender_id, created_at, original vs. translated)' + ticket 006 (frontend rendering) acceptance: 'Message thread renders with sender name, original language, dual-text display'

**Frontend Impact (Tweedledee):**

I need: sender_id to render sender identity, text_original and text_translated to show side-by-side, translation_status and translation_error to show warning UI when vendor fails. Sender-sees-own-message-in-original is a rendering rule on my side (check current_user == sender_id); I don't need separate fields for that. Length variance between original and translated is a layout concern (flexbox handles it). Open question: should sender see translation_error for their own messages, or only receivers? This affects warning UI placement.

**Backend Impact (Tweedledum):**

I need to implement the synchronous translation call here. On GET /conversations/{id}/messages?read_language={lang_code}, I iterate the returned message set and call vendor for each message where sender's language != read_language. All translation happens here, in the read path. Implication: GET latency scales with number of untranslated messages × vendor latency. Mitigation: fast-follow caches Translation results in a separate table (Translation(id, message_id, target_language, text_translated, cached_at)) so repeated reads of the same message don't re-call vendor. For MVP, I accept the latency hit because receiver count is small. Critical invariant: text_original is always populated and immutable (sender's original text, never translated). text_translated is computed on-read and populated or null depending on vendor success. Regarding your open question (sender sees translation_error for own messages?): I'm proposing NO — sender sees text_original populated and text_translated empty (no error). Receiver sees the full envelope including translation_error if it failed. Rationale: sender doesn't need to know translation failed; if they care about translation quality, they can see what receiver gets by switching to read-language perspective. This simplifies the response shape (no error fields for sender, only for receiver). Does this composition work for you?
