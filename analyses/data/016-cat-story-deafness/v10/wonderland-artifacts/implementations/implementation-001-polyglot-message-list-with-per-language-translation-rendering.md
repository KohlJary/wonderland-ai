## Implementation 001: Polyglot message list with per-language translation rendering

**Side:** frontend
**Ticket:** ticket-003
**Contract:** message-envelope v1 (locked via contract-note-001 and contract-note-002): {id, author_id, original_text, original_language, translations: {lang_code: {text, status}}, translation_status: enum summary, created_at}. Single-fetch query semantics; no per-language JOINs. ADR-001 + ADR-003 commitments: third-party translation (EU-hosted), polyglot mesh routing, no silent English pivoting.
**Ready for review:** no

**Approach:**

Render messages with original text + translations for the user's active language preferences. Each translation carries its own status badge (pending/complete/failed). Loading state is per-language, not per-message. When a translation is pending, show a skeleton or 'translating...' indicator; when complete, show the translated text; when failed, show the original text with a 'translation unavailable' badge. The query returns the full translations JSONB; I filter for languages the user is actively reading (user preference set + source-message language for context). Status summary enum on the message lets me show an aggregate badge (e.g., 'partially translated') when not all languages are ready.

**UI States Implemented:**
- loading: skeleton placeholder while translation_status=pending for the user's active language
- complete: translated text displayed with translation complete badge
- error-recoverable: original text displayed with 'translation unavailable' badge when status=failed; user can refresh
- stale: if user changes preferences mid-thread, existing translations shown or new fetch triggered on next view
- pending: message renders original text while first translation is computing (SLA ~5s); user sees 'translating...' indicator

**Client State:**

MessageListContext holds user's active language preferences (set via signup/settings flow). Per-message, the translations JSONB is fetched once and cached locally until user explicitly refreshes or changes preferences. No client-side duplication of translation state; the source of truth is the server message record. Loading state for in-flight translations is computed per-language by checking the status substatus in the translations JSONB, not stored separately on the client.

**Files:**
- src/components/MessageList.tsx: render original_text + translations[user_language] with per-language status badges
- src/hooks/useMessageTranslations.ts: filter translations JSONB for active user languages, compute loading/error states per-language
- src/types/message.ts: type Message with translations JSONB shape, translation_status enum
- src/styles/messageList.module.css: loading skeleton for pending translations, failed-translation styling

**Open Questions for Pair:**
- When a user's language preferences change mid-thread (e.g., EN→JA), should the message list re-fetch to get JA translations for previously-viewed messages, or accept stale EN-only rendering until next refresh? (Contract assumes lazy-consistency acceptable for v1.)
- Translation_status enum: should I use the summary enum on the message record, or compute the summary on the frontend by checking all language statuses in translations? (Schema suggests it's computed/stored on your side for audit purposes; I can compute independently for rendering if needed.)

**Known Limitations:**
- error-recoverable: failed translations show original text + 'translation unavailable' badge; no user-facing retry button (v2). User can try refreshing the message list.
- stale-after-preference-change: if user switches language preferences mid-thread, they see existing translations for new language (if computed) or stale/absent translations until refresh. Acceptable for v1.
- no-audit-view in this implementation: Marcus's moderation view (seeing all translations + status for a message) is a separate code path, to be implemented after message-list is reviewed.
