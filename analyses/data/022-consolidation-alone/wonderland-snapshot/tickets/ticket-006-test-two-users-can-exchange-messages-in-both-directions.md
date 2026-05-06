## Ticket 006: Test: two users can exchange messages in both directions

**Sources:** story/english-speaker-initiates-a-chat-with-a-german-speaker, story/conversation-is-persistent-and-both-users-see-the-full-history, story/second-language-pair-works-the-same-way-english-japanese
**Owner:** Mad Hatter
**Tier:** v1
**Estimate:** 1–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/set-up-http-basic-auth-signup-login-endpoints, ticket/initiate-a-new-conversation-with-another-user, ticket/create-messages-and-conversations-schema-add-send-message-endpoint, ticket/fetch-messages-in-a-conversation, ticket/list-users-conversations-with-last-message-preview
- Soft: —

**Description:**

End-to-end test: Alice (EN speaker) initiates a conversation with Klaus (DE speaker). Alice sends 'Hello Klaus' in English. Klaus receives the message with German translation. Klaus replies 'Hallo Alice' in German. Alice receives the message with English translation. Both users see the full conversation history when they fetch the conversation. Test both language pairs (EN↔DE and EN↔JA from Story 003). Test that users see only their own conversations (no cross-conversation leakage).

**Acceptance:**
- Alice can sign up, log in, initiate a conversation with Klaus
- Klaus can log in, see the conversation from Alice, and send a reply
- Alice receives Klaus's reply with English translation
- Klaus receives Alice's original message with German translation
- GET /conversations returns the same conversation for both users
- Each user's conversation list shows only their own conversations
- EN↔DE pair works; EN↔JA pair works

**Risk:**

Translation API availability. If the API is down, this test will fail. Mock the API for test environment; do not depend on a real API endpoint in the test. If the team hasn't picked a translation provider yet, this ticket is blocked.
