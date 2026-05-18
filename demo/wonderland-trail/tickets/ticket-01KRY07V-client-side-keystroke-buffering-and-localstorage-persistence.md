## Ticket 068: Client-side keystroke buffering and localStorage persistence

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2E
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-kohl-drafts-notes, story-persistent-backup
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: save-endpoint-atomic-writes
- Blocked by: —
- Soft: —

**Description:**

Implement keystroke buffering in the note editor. Buffer keypresses locally to avoid sending every keystroke to the backend. Persist buffer to localStorage on interval (every 2 seconds or on blur). On page load, check for buffered content and surface if it exists. No network calls yet — this is local durability only.

**Acceptance:**
- Keypresses are buffered locally in memory and to localStorage
- Buffer persists across page reload
- User sees buffered content on return if unsaved

**Risk:**

React re-render behavior with large buffers — may need debouncing tuning if keystroke volume is high.
