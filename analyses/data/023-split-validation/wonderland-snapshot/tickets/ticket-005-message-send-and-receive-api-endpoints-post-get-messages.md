## Ticket 005: Message send and receive API endpoints (POST/GET /messages)

**Sources:** story: user-receives-a-message-from-someone-speaking-a-language-they-don-t-speak, story: polyglot-moderator-manages-multi-language-thread
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5-2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-conversation-and-message-rendering
- Blocked by: translation-service-integration-and-vendor-contract
- Soft: —

**Description:**

Implement POST /conversations/{id}/messages (sender writes message in their language) and GET /conversations/{id}/messages?read_language=de (receiver reads conversation with auto-translation). Frontend integration: sender sees own message in original language; receiver sees translated. Both languages shown side-by-side for transparency (matches Sophie's confusion-flag requirement). No edit/delete in v1.

**Acceptance:**
- POST /conversations/{id}/messages accepts {text, language} and stores in Message table
- GET /conversations/{id}/messages?read_language=de returns message list with both original and translated text
- Sender identity is enforced (cannot send as someone else)
- Translation errors are handled gracefully (original text returned + warning)
- Response includes metadata for frontend (sender_id, created_at, original vs. translated)

**Risk:**

Frontend rendering contract (what fields does frontend expect?) must be locked before Tweedledee starts. Includes in contract note per Pair Protocol.
