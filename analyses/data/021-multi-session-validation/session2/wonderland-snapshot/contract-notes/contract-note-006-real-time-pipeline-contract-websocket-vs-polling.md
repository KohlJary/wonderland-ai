## Contract Note 006: Real-Time Pipeline Contract (WebSocket vs Polling)

**State:** proposed → responded
**Contract Version:** (unlocked)

**Current Shape:**

Ticket 004 names the choice as open but doesn't specify the contract shape.

**Proposed Change:**

Two candidate contracts; your preference drives implementation.

**Option A: WebSocket**
- Frontend connects: `WebSocket /ws?session_token=<token>`
- Backend authenticates token on connect; if invalid, close 401
- Backend sends message events: `{ event: 'message_created', data: { ...message envelope } }`
- Frontend sends message: `{ event: 'message_send', data: { chat_id, original_text } }`
- Backend receives, persists, translates (async or sync per contract 1), emits message_created event
- Latency: single round trip for send; subsequent translation is an async update event (if async) or included in initial response (if sync). Target SLO: <2s from send to receive.
- Connection loss: frontend detects (TCP half-close or heartbeat timeout); renders 'disconnected' indicator; reconnect on user action or automatically
- Scaling: WebSocket requires server to hold N connections; in production, use Redis pub/sub to fan out across server instances. Out of scope v1.

**Option B: Polling**
- Frontend polls `GET /chats/{chat_id}/messages?since=<timestamp>` every N seconds (e.g., 1–2s)
- Backend returns array of messages created since `since` (with pagination)
- Latency: up to N seconds delay before user sees a message, plus network RTT. For 2s polling, worst case is 4s. May not hit <2s SLO.
- Advantage: stateless (no connection memory); easier to scale; simpler error handling
- Disadvantage: higher latency; higher server load (many GETs)

**Current proposal: WebSocket for v1** (better latency, acceptable complexity for MVP). If you prefer polling, it's simpler but may violate the <2s SLO on message delivery. Flag if polling is your preference.

**Message ordering:**
Backend returns messages ordered by created_at (ascending). Frontend renders in that order. If two messages arrive with the same created_at (clock skew), order is undefined; v1 accepts this. (Deterministic ordering via sequence numbers is deferred to fast-follow.)

**Chat join/leave semantics:**
V1 assumes a two-user chat that persists for the session. User A and User B are matched by language pair; both are in the chat for the duration of the session. No explicit join/leave; session end is implicit (timeout or user closes app). ADR decides whether the chat persists after session end (indefinite persistence with later user join) or is ephemeral (deleted when last user leaves). Current assumption per ADR: chat persists indefinitely; later (post-v1) users can query historical chats. If this is wrong, the message envelope and chat model need revision.

**Source:** Ticket 004 names the contract as the critical uncertainty for the message SLO. ADR leaves message persistence strategy open (are chats ephemeral or indefinite?).

**Frontend Impact (Tweedledee):**

I'm **asserting WebSocket is necessary** for the <2s SLO and the user experience. Polling with 1–2s interval risks 4s worst-case latency; that's double the target. WebSocket at <2s is tight but achievable (one RTT for send, translation is async update per contract 004).

**WebSocket handling:**

- **Connection lifecycle:** On app load (after login), I establish `WebSocket /ws?session_token=<token>`. I parse the session_token from localStorage. Backend validates on connect; if 401, show error ("Authentication failed, please re-login"). On success, I'm connected and ready.

- **Send flow:** User types message, clicks send. I emit `{ event: 'message_send', data: { chat_id, original_text } }` on the socket. Backend persists message and returns `{ event: 'message_created', data: { message object with id, sender_id, translation_status='pending', ... } }`. I add the message to my local list immediately (optimistic update). If translation completes while WebSocket is still open, I get a second event (contract 004 detail): `{ event: 'message_translation_complete', data: { message_id, translation_status='translated', translated_text } }` and I update the message in-place.

- **Receive flow:** Messages from the other user arrive as `{ event: 'message_created', ... }`. I add to my local list. If translation arrives later, same update flow.

- **Connection loss handling:** I'll add heartbeat detection (either backend sends periodic ping, or I send periodic heartbeat ping). If no response for 5s, I consider the connection lost and show a "Disconnected" indicator in the UI. Reconnect is **manual for v1**—user clicks "Reconnect" button. (Automatic reconnect is a nice-to-have fast-follow.)

- **Offline queueing:** If user types a message while disconnected, I **queue it locally** (store in localStorage). On reconnect, I replay the queue. This is a UI state: "pending-sync" for messages that haven't been sent yet. Hatter will need to test this flow.

- **Message ordering:** I'll store messages in a list keyed by created_at. Backend sends ordered by created_at ascending. If two messages have the same created_at (clock skew), I'll accept undefined order for v1 and note it as a known limitation.

**Client state for real-time:**
- `websocket_connected: boolean` — renders the "Disconnected" indicator
- `messages: [ { id, created_at, sender_id, sender_name, original_text, translated_text, translation_status, ... } ]` — the message list
- `pending_messages: [ { local_id, original_text, timestamp } ]` — queued while disconnected (not persisted yet)
- `chat_id: UUID` — the active chat

**Open questions for backend:**
1. When I connect via WebSocket, does the backend immediately send me the chat history (backfill), or do I need to HTTP GET /chats/{chat_id}/messages on connect and then listen for new messages? I'm assuming backfill-on-connect for simplicity.
2. When async translation completes (contract 004), what's the exact event shape? `{ event: 'message_translation_complete', data: { message_id, translation_status, translated_text } }`? Or do I get a full message object re-sent?
3. Heartbeat: do you send periodic `{ event: 'ping' }` and expect me to respond with `{ event: 'pong' }`, or the other way around?

**Backend Impact (Tweedledum):**

Backend owns WebSocket lifecycle (auth on connect, connection heartbeat, disconnect handling), message emission on create, and polling endpoint (if Option B). If WebSocket + async translation (per contract 1), backend emits a second update event when translation completes. If polling, backend's GET /chats/{id}/messages must be efficient (index on chat_id + created_at).

---

**Tweedledee's assessment:** I'm **marking WebSocket as mandatory** and **ready to agree** pending clarification on: (1) do you backfill chat history on WebSocket connect, or do I fetch separately? (2) exact event shape for translation completion? (3) heartbeat direction/format? These are small details; once clarified, contract is locked.
