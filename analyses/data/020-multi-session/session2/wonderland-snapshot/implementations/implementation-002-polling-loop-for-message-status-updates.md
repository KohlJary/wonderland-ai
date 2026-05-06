## Implementation 002: Polling loop for message status updates

**Side:** frontend
**Ticket:** frontend-polling-loop-for-message-status-updates
**Contract:** message-envelope v1; polling endpoint GET /conversations/{conversation_id}/messages returns array of messages sorted by created_at descending; poll only occurs when conversation is in focus (minimizes backend load)
**Ready for review:** no

**Approach:**

React hook (useMessagePoll) that polls GET /conversations/{conversation_id}/messages every 2 seconds. Detects messages with translation_status=pending_translation and re-polls until they reach translated or translation_failed. Implements exponential backoff on network errors (max 10 seconds between polls). Updates a messages array in local component state; Message components re-render when their object changes. Unsubscribes on unmount.

**UI States Implemented:**
- loading: initial render before first poll completes
- polling: messages visible, background poll in progress
- poll_error_recoverable: previous message list shown, retry in progress
- poll_error_unrecoverable: error message shown, user can retry manually

**Client State:**

messages array (list of message objects keyed by id), pollIntervalId (timer id for cleanup), lastPollTimestamp (for deduplication). Reconciliation on each poll: compare incoming message.id against local cache; update if translated_at differs, add if new, remove if absent from response. Cache is in-memory and cleared on component unmount.

**Files:**
- src/hooks/useMessagePoll.ts: polling loop hook with interval management, error handling, backoff
- src/components/Conversation.tsx: integrate useMessagePoll, pass message array to child Message components

**Open Questions for Pair:**
- When a message translation completes, does the API return the full message object with updated translated_text in that same poll response, or do we need a second poll to fetch it?
- Should the frontend cache the full message list and only update changed messages, or fetch fresh on each poll? (affects reconciliation logic and backend load)

**Known Limitations:**
- 2-second polling interval is hardcoded; no adaptive polling based on user idle/focus (v2 optimization)
- No deduplication of in-flight polls; rapid conversation switches could queue multiple polls (medium severity — can cause momentary message duplication in state)
- Offline detection not yet implemented; polling continues even without network (polling will fail gracefully, but no user feedback)
