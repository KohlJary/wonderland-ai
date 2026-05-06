## Implementation 001: Message render component with bidirectional language display

**Side:** frontend
**Ticket:** frontend-message-render-component-with-bidirectional-language-display
**Contract:** message-envelope v1 (original_text, translated_text, translation_status, sender_id, receiver_id implicit, language_pair, created_at, translated_at nullable, error_code nullable, error_message nullable)
**Ready for review:** no

**Approach:**

React component that accepts a message object (per agreed envelope: original_text, translated_text, translation_status, sender_id, language_pair) and current_user_id. Renders sender's perspective (always original_text in sender's language) or receiver's perspective (translated_text with source attribution). Handles pending_translation state with spinner; translated state with full text and source label; translation_failed state with original text and error notice. No client-side state manipulation — component is pure render of the message object passed in.

**UI States Implemented:**
- pending_translation: original text visible, spinner overlay, 'translating...' label
- translated: translated text visible, source attribution below, original on hover/expand
- translation_failed: original text visible, error icon, 'translation failed' notice with error details
- loading: skeleton placeholder while message object is being fetched

**Client State:**

No persistent client state. Message objects are cached in memory in the parent Conversation component; reconciliation happens on each polling response by comparing message.id and message.translated_at timestamp. New or updated messages replace stale versions; deleted messages are removed. Cache is cleared on conversation unmount.

**Files:**
- src/components/Message.tsx: message render component with conditional language display based on translation_status
- src/components/Message.module.css: styling for pending/translated/error states with visual indicators

**Open Questions for Pair:**
- Does the API ever return a message with translation_status=pending_translation AND translated_text populated (i.e., partial translation)? If so, which do we display — partial or wait for full?
- For error_message from translation service — is this always user-facing text, or sometimes technical codes? Should we surface it directly or map to a friendly message?

**Known Limitations:**
- Component assumes language_pair is always sender_language→receiver_language; doesn't yet handle symmetric conversations (low severity — architecture guarantees this)
- Error notice styling is placeholder; Queen's ruling on security/compliance language display not yet reviewed (medium severity — blocking review)
- No copy-to-clipboard or quote-reply surfaces yet (deferred to v2)
