## Ticket 004: Frontend: Message render component with bidirectional language display

**Sources:** story-001, story-002, adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1.5–2.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-006
- Blocked by: —
- Soft: ticket-003

**Description:**

Create Message component that renders both original_text and translated_text, labeled by language. If sender's language matches user's language preference, show original_text first; if receiver's language matches, show translated_text first, with attribution label ('Original: [original text]'). Handle translation_status: if pending_translation, render message with 'translating...' indicator; if translated, show both languages; if translation_failed, show original_text with error notice and offer to refresh. Implement optimistic render: show message immediately after send with sender's language, translation_status = pending_translation, and loading indicator.

**Acceptance:**
- Sender sees original_text in sender's language immediately after send
- Receiver sees translated_text in receiver's language with 'Original:' attribution
- Pending messages show 'translating...' indicator
- Failed translations show error and fallback to original_text
- Language preference is read from user context (not hardcoded)
- Component is reusable across conversation threads

**Risk:**

If translation_status updates are slow (polling latency), 'translating...' indicator may appear stale. Mitigated by 2-4s polling interval (see ticket-006). If language preference is stored in multiple places, sync bugs are likely — ensure single source of truth.
