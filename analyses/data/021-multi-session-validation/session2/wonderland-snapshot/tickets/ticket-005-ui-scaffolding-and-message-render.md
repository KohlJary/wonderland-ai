## Ticket 005: UI scaffolding and message render

**Sources:** story:exchange-messages-with-a-german-speaker, story:exchange-messages-with-a-japanese-speaker, story:see-who-i-m-talking-to-and-when
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1.5–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:message-send-receive-pipeline
- Soft: ticket:user-registration-and-auth-email--password-v1

**Description:**

Build basic chat UI: login form, message list, message input, send button. Render messages with sender name, timestamp, and translated text (if available). Assume single chat per session (no room selection in v1). Show translation status: original, translated, translation failed. No styling beyond readability; no dark mode, no responsive design in v1 (desktop focus). Coordinate with Tweedledum on the real-time pipeline to know when to re-render.

**Acceptance:**
- Login form renders and accepts email + password
- Message list displays all messages in a chat with sender, timestamp, original, and translated text
- Send button inserts a message into the input and triggers send
- UI updates in real time when new messages arrive (or on next poll)
- Translation status is visible (original, translated, failed)

**Risk:**

If translation service latency is high, message renders may stall waiting for translation. Coordinate with Tweedledum on whether frontend should render original immediately and update when translation arrives.
