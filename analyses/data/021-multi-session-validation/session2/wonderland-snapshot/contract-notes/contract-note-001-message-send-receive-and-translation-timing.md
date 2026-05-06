## Contract Note 001: Message send/receive and translation timing

**State:** proposed (awaiting resolution)
**Contract Version:** (unlocked)

**Current Shape:**

ADR assumes backend translation via external service (DeepL), but timing is open: sync (translate before send, latency += service latency) vs async (send original, translate in background, re-send translated).

**Proposed Change:**

Frontend needs explicit contract on message flow: (A) sync model — frontend sends message, waits for response with both original and translated_body; (B) async model — frontend sends message, receives original, gets translation_status='pending', then receives update event with translated_body when ready. Ticket 004 estimates 2-3 days assuming contract is clear; latency budget is <2s send-to-receive on stable network. If translation adds >1s, async becomes non-negotiable.

**Source:** ticket:message-send-receive-pipeline + ADR tradeoff on translation service risk. Ticket 004 lists latency <2s as acceptance criterion; translation timing drives feasibility.

**Frontend Impact (Tweedledee):**

Sync model: frontend waits for translated_body in send response, renders message once. Simpler state machine, but if translation timeout occurs, entire send is visible-failed to user. Async model: frontend renders original immediately (pending state), then updates in-place when translation arrives. More complex state (message_translation_status enum: original / translated / translation_failed), but graceful degradation (user sees something immediately). For <2s target, async is safer.

**Backend Impact (Tweedledum):**

Going async. Here's why and what it commits:

Translation service latency budget (per ticket 003): DeepL API is ~400-800ms in nominal conditions, but tail latencies are 1-2s and service outages happen (seen in prod). Sync-before-send would mean every message send blocks on a 1-2s API call—that violates the <2s send-to-receive SLO on its own. Instead:

**Message send (POST /chats/{chat_id}/messages):**
- Request: `{ original_text (string), original_language (enum: EN, DE, JA) }`
- Response (200): `{ id (UUID), chat_id, sender_id, original_text, original_language, translated_text (null), translation_status ('pending'), created_at }`
- Backend persists message synchronously (message table: INSERT with translation_status='pending')
- Backend enqueues async translation job immediately (e.g., Celery task or post-insert hook)
- Return within 100ms (target: persist + enqueue < 100ms; send-to-response < 200ms including network RTT)

**Async translation job:**
- Calls DeepL API with 3s timeout (per ticket 003)
- On success: UPDATE messages SET translated_text = ..., translation_status = 'translated', updated_at = now()
- On failure (timeout or service error): UPDATE messages SET translation_status = 'failed', translation_error = '...', updated_at = now()
- Emits WebSocket event (per contract 006): `{ event: 'message_translated', data: { message_id, translated_text, translation_status } }` to both users in the conversation
- Translation job is fire-and-forget; message is not blocked

**Deletion semantics (GDPR 17):**
- When user deletes a message via DELETE /messages/{message_id}, soft-delete: UPDATE messages SET deleted_at = now()
- If translation job is in flight (translation_status='pending'), it completes, but when the message is read, it's marked deleted—so frontend won't render it
- Deletion cascade: if a user account is deleted (GDPR subject request), delete all messages with that sender_id
- Translation cache: we're not caching translations in v1 (per ticket 003), so no purge needed. If cache is added later, deletion must trigger a purge request to the translation service. For now: no action needed on deletion beyond soft-delete + cascade.

**Error handling:**
- If translation job crashes (bug, not timeouts): logged and counted in metrics; message stays with translation_status='failed'. Frontend renders original text with error indicator.
- If enqueue fails (queue full, etc.): message is persisted with translation_status='pending', but job is not enqueued. Frontend sees 'pending' indefinitely. Mitigate by monitoring queue depth and alerting. This is a known limitation for v1.

**Known limitations:**
- Translation is best-effort async. If the system crashes after persisting a message but before translation completes, that message may never get translated. We accept this for v1 (operational cost of improved latency).
- No retry on translation job failure. If the job fails, it stays failed. Retry logic (exponential backoff, dead-letter queues) is deferred to fast-follow.
- No deletion of already-translated content from translation service cache because we're not caching. This is correct for v1.

**Contract specifics (for message envelope):**
Message object returned by backend always includes:
- `id, chat_id, sender_id, original_text, original_language, translated_text (null if pending/failed), translation_status (enum: 'pending', 'translated', 'failed'), translation_error (null if not failed), created_at, updated_at`

**Questions for Tweedledee:**
- Can you handle the async model on the frontend? (render original immediately, then update when translation arrives)
- What's your tolerance for the "pending indefinitely" edge case if the queue is full?
- Does WebSocket event `message_translated` work for you, or do you prefer polling the message endpoint?

**Resolution:** proposed — awaiting frontend response on async model feasibility and WebSocket event handling.
