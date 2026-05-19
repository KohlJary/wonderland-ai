## Ticket 085: useBootNotes comments incorrectly describe scope of localStorage merge logic; actual merge happens in Editor, not here

**GUID:** 01KRY1TKADRB6DBQR5AGRJVCFA
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, kohl-drafts-and-saves-experimental-notes-with-persistent-backup-cross-ticket-coherence-and-implementation-review
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

From review ``kohl-drafts-and-saves-experimental-notes-with-persistent-backup-cross-ticket-coherence-and-implementation-review`` (change-required):

**Concern:** The original comment (in the diff) was longer and more complex, describing a 'merge strategy (OPTIMISTIC)' with details about buffer precedence logic. The new comment correctly simplifies it to 'useBootNotes loads the list; Editor handles per-note merge.' This is clearer, but the removal of the old strategy description means a future developer might not know WHY the responsibility is split. Adding one sentence about the rationale would help.

**Request:** Enhance the comment with rationale: 'Per-note buffer merging is delegated to the Editor component when a specific note is opened because: (1) useBootNotes operates at global scope (entire note list), but merge reconciliation is per-note; (2) Editor has access to both the specific note's server state and the corresponding localStorage buffer; (3) this separation of concerns keeps useBootNotes simple (fetch + return) and Editor focused (load, merge, edit).' This is a documentation improvement, not a code change.

**Location:** ``frontend/src/useBootNotes.ts:5-17``

**Acceptance:**
- Enhance the comment with rationale: 'Per-note buffer merging is delegated to the Editor component when a specific note is opened because: (1) useBootNotes operates at global scope (entire note list), but merge reconciliation is per-note; (2) Editor has access to both the specific note's server state and the corresponding localStorage buffer; (3) this separation of concerns keeps useBootNotes simple (fetch + return) and Editor focused (load, merge, edit).' This is a documentation improvement, not a code change.
