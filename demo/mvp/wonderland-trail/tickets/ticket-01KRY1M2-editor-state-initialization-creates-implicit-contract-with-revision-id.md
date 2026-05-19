## Ticket 079: Editor state initialization creates implicit contract with revision_id

**GUID:** 01KRY1M2ZH1E7644RHB7R1R8WQ
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup`` (change-required):

**Concern:** The Editor component has three sources of truth: (1) backend loaded via readNote (has current revision_id), (2) localStorage keystroke buffer (may have stale revision_id), (3) server state loaded on conflict (has current revision_id). When the Editor chooses 'keep_buffer' in a conflict, it sets revision_id to null. This is correct because the buffer may have been edited since the last successful save, so its old revision_id is not valid. But if a keystroke buffer is restored on mount without conflict, its cached revision_id is used, which could be stale if the note was edited elsewhere (e.g., on another device). The code handles the case where server is newer (it discards the buffer), but doesn't handle the case where the buffer's revision_id is simply outdated because the note was edited in another session on the same device.

**Request:** Add a comment clarifying the revision_id invariant in EditorState: 'revision_id is null for new notes and for buffers whose revision_id is unknown or stale (e.g., restored from localStorage). On successful save, revision_id is set to the server response. On conflict, revision_id is set to null because the buffer is in an uncommitted edit state.' This is defensive documentation that will protect future readers (and you in three months) from the temptation to trust a stale revision_id from localStorage.

**Location:** ``frontend/src/Editor.tsx:52``

**Acceptance:**
- Add a comment clarifying the revision_id invariant in EditorState: 'revision_id is null for new notes and for buffers whose revision_id is unknown or stale (e.g., restored from localStorage). On successful save, revision_id is set to the server response. On conflict, revision_id is set to null because the buffer is in an uncommitted edit state.' This is defensive documentation that will protect future readers (and you in three months) from the temptation to trust a stale revision_id from localStorage.
