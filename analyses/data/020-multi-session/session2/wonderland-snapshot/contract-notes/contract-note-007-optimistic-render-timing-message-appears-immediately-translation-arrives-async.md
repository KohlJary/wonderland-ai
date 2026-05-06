## Contract Note 007: Optimistic Render Timing: message appears immediately, translation arrives async

**State:** agreed
**Contract Version:** optimistic-render v1 (sync return with pending_translation, async translation service, eventual update via poll)

**Current Shape:**

Skeleton returns message immediately (implied synchronous), status unknown.

**Proposed Change:**

When frontend sends a message (POST /conversations/{id}/messages or similar), backend returns synchronously with Message(sender_id, original_text, translated_text='', language_pair, translation_status='pending_translation', created_at, translated_at=null, error_code=null). Frontend immediately renders this message with 'translating...' indicator. Backend then asynchronously calls the translation service (within ~1 second of message creation). On translation completion, backend updates the Message record (translated_text is populated, translation_status→'translated', translated_at is set). Next time frontend polls (within 2 seconds), it receives the updated message and re-renders with the translation visible. This contract requires: (1) backend returns the pending message synchronously, (2) translation service call is async/background, (3) frontend expects to see translation_status change on the next poll.

**Source:** adr-001 (async translation state machine); ticket-001 (schema); ticket-002 (service integration); story-001 (Klaus needs 2-3 sec, message must appear immediately); story-002 (Yuki needs 3-5 sec tolerance, same pattern)

**Frontend Impact (Tweedledee):**

Frontend must handle optimistic render: when user sends a message, the UI shows it immediately with 'translating...' indicator, even though translation_status=pending_translation and translated_text is empty. Frontend does NOT wait for backend response to show the message; the response is used to populate the sent message's ID and created_at (for reference). The message object is created locally, sent to backend, and then tracked via polling. Polling observes when translation completes and updates the UI without user intervention. No manual 'refresh' button needed — the polling loop is the refresh mechanism.

**Backend Impact (Tweedledum):**

When POST /conversations/{id}/messages arrives, backend immediately persists the message with translation_status='pending_translation', translated_text='', and returns the full message object synchronously (include the message_id and created_at so frontend knows the identity of what it sent). The synchronous response closes the HTTP request. Asynchronously (in a background worker or job queue), backend calls the translation service, waits for completion (with timeout ~5 seconds, retries up to 3 times), and updates the message record with translated_text and translation_status='translated' (or status='translation_failed' if the service fails after retries). Frontend observes this change on the next poll (within 2 seconds). The invariant: message is queryable and visible immediately; translation is eventual. Failure mode handled: if translation service is slow or unavailable, the message is still readable (original_text is always present), and the user gets error visibility (translation_failed status, optional error notice).

**Resolution:**

Frontend optimistic render (show message immediately, update on poll) matches backend async workflow (sync return pending, async translation, eventual update). Message is readable immediately; translation is eventual. Contract is locked.
