## Ticket 006: Offline message queue for polyglot threads (fast-follow)

**Sources:** story/polyglot-moderator-manages-cross-language-thread-without-drowning
**Owner:** Tweedledum
**Tier:** fast-follow
**Estimate:** 1.5–2.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/translation-backend
- Soft: ticket/polyglot-moderator-frontend

**Description:**

The polyglot-moderator story mentions 'checking messages offline.' Scope for fast-follow: local message queue that captures incoming messages when network is unavailable, syncs and translates them when connectivity returns. Out of scope: sync conflict resolution, offline composition, stale message handling. Minimally viable: user goes offline, messages arrive, user comes back online, queue syncs and shows translated messages.

**Acceptance:**
- Offline queue persists messages locally
- Sync on reconnect translates and displays queued messages
- No duplicate messages after sync
- Queue clears after successful sync

**Risk:**

Moderate. Offline detection and sync logic can be finicky. Expand estimate if device-level battery/connectivity APIs prove unreliable.
