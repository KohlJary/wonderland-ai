## Contract Note 002: Message receive response envelope (GET /conversations/{id}/messages?read_language=de)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

GET accepts query param ?read_language=lang_code. Returns array of {id, sender_id, text_original, text_language, created_at, text_translated, translation_status}. translation_status in [success, error_original_returned]. If translation fails, text_translated is null and status is error_original_returned; frontend shows original + warning. Always includes both text_original and text_translated so frontend can show transparency (per Sophie's confusion-flag). Filters soft-deleted messages (WHERE deleted_at IS NULL).

**Source:** ticket-003 (translation surface) + ticket-005 (rendering contract) + story-001 (Sophie's transparency need)

**Frontend Impact (Tweedledee):**

I render message list with: sender_id (to identify who sent), text_original, text_translated (both shown side-by-side per story-001), translation_status. If translation_status=error_original_returned, I show a warning badge next to the original text: "Translation unavailable—showing original." For sender's own messages, I always show text_original (user sees what they typed). For receiver's messages, I show both text_original and text_translated (transparency). When read_language parameter is provided, I filter conversation's messages by that language. Open question: should the GET response include sender_name, or do I fetch user details separately? Current envelope includes sender_id but not sender_name. If I need to show sender identity in the UI, do I make a separate call to fetch User details, or should POST/GET envelope include sender_name? Proposing: GET includes sender_id only (keep envelope lean); if I need sender name, I cache user lookups client-side or in a separate /users/{id} request. This keeps the message contract narrow and the user contract separate.

**Backend Impact (Tweedledum):**

For each message, calls translation service synchronously to translate text_original from text_language to read_language. Caching translation results is fast-follow (MVP: on-demand). On vendor error (timeout, rate limit, invalid key): returns original text, sets translation_status=error_original_returned, frontend shows warning. Handles vendor latency (target <500ms; if observed >500ms in prod, fast-follow caches). Query must filter deleted_at IS NULL.
