## Ticket 003: Frontend: Message input and conversation render (monolingual view)

**Sources:** 001-two-monolingual-users-exchange-messages-in-their-native-language, 003-user-sees-their-message-in-the-language-they-sent-it-not-re-translated-back-to-them
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-message-schema-and-storage
- Soft: define-message-translation-api-contract-for-two-user-exchange

**Description:**

Build the chat UI component: message input field (text + hidden language selector, defaulting to user's language preference), conversation render (display messages in thread, each showing original_language + original_text; translation field renders as empty or placeholder for now). Support Klaus→Maya and Maya→Klaus scenarios: Klaus types in German, hits send, sees his message appear in German immediately (no re-translation to himself). Maya receives Klaus's message, sees the German original + a placeholder for translation. Once translation routing is wired, this component renders translation without changing. No real-time WebSocket yet — use polling (GET /conversation on 2s interval). This is sufficient for v1; real-time is fast-follow pending translator latency SLO.

**Acceptance:**
- User can type a message and send it; message appears in conversation thread immediately in the language sent
- GET /conversation polling refreshes the view every 2s
- Messages from other users appear with original_language and original_text rendered visibly
- Translation field is present in the render but empty / placeholder text ('Translation pending...')
- Scenario: Klaus sends German, sees German immediately. Maya receives, sees German + placeholder.

**Risk:**

Polling at 2s interval will feel slow for fast exchanges. We're accepting this for v1. Real-time (WebSocket) is blocked on translation latency — once we know how fast translation actually is, we can decide if 2s polling is acceptable or if we need to upgrade. If translation is sub-500ms, polling is fine. If it's 2-5s, we need WebSocket.
