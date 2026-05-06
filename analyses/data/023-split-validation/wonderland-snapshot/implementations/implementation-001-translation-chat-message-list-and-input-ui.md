## Implementation 001: Translation chat message list and input UI

**Side:** frontend
**Ticket:** ticket-005-message-send-and-receive-api-endpoints
**Contract:** contract-note-004 (GET response envelope), contract-note-005 (POST request envelope), contract-note-006 (translation error handling). Endpoints: POST /conversations/{conversation_id}/messages {text, language}, GET /conversations/{conversation_id}/messages?read_language={lang}. Response includes text_original, text_translated, translation_status, translation_error, sender_name.
**Ready for review:** yes

**Approach:**

React components using TypeScript. api.ts wraps fetch calls to POST and GET /conversations/{id}/messages with proper error handling. App.tsx component manages message list state, language preferences (send/read), and form submission. MessageItem component renders individual messages with both original and translated text, sender name, timestamp, and translation error warnings. Language selectors allow user to choose which language to read messages in and which language to send in. Client state: draft text, read_language, send_language, messages list. Reconciliation: POST response is used immediately to append message; GET refetch when language preference changes.

**UI States Implemented:**
- loading: shows 'Loading messages…' while GET is in progress
- empty: shows 'No messages yet. Start the conversation!' when list is empty
- success: messages rendered with both original and translated text
- error-recoverable: translation error shows warning box with translation_error message; user can refresh to retry
- draft: input field shows draft text; send button disabled until text is non-empty

**Client State:**

messages: Message[] (from GET response, refetched when read_language changes); draft: string (input field text); readLanguage: string (user's preference for reading language, controls GET query param); sendLanguage: string (user's preference for sending language, controls POST body). Reconciliation: when read_language changes, GET is called with new language and messages are replaced. When message is sent, POST returns message object which is appended to list immediately (no translation yet), then if user changes read_language, full refresh happens and message will be translated.

**Files:**
- frontend/src/api.ts: New request/response types (Message interface), functions for postMessage(conversation_id, text, language) and listMessages(conversation_id, read_language)
- frontend/src/App.tsx: App component with language selectors, message input form, message list rendering. MessageItem component for individual message display with both texts, sender metadata, and translation error UI.

**Open Questions for Pair:**
- Hardcoded conversation_id=1, user_id=1, language_pair=['en','de'] for MVP. When should we add real conversation picker and auth? Currently acceptable for seed verification, but blocking actual multi-conversation use.
- Translation latency: GET currently waits for all messages to be translated. If latency becomes noticeable with many messages, we might want WebSocket updates or pagination. Contract supports this; backend can optimize later with caching.

**Known Limitations:**
- Hardcoded conversation context (conversation_id=1, user_id=1) — real auth and conversation routing needed for production (ticket for fast-follow)
- No real-time updates — user must refresh to see new messages (WebSocket polling is fast-follow, per story-005)
- No offline message queue (fast-follow per story-005)
- Language selectors are static hardcoded pair (en_de) — should be fetched from conversation metadata when available
