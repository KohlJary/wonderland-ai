## Ticket 078: useBootNotes merging logic incomplete vs. contract description

**GUID:** 01KRY1M2Z4JE4W8HHZ2GNQ0EGG
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

**Concern:** The function's contract (in its JSDoc) and implementation diverge. Callers reading the JSDoc will expect merge logic that doesn't exist. This creates two problems: (1) future readers of the code will be confused about what the function actually does, and (2) if Kohl uses two tabs and has a keystroke buffer in one while the other is loading, the buffer will be silently discarded.

**Request:** Either: (A) implement the merge logic described (iterate backend notes, check localStorage buffers per note, apply merge strategy), or (B) simplify the JSDoc to match the implementation ('loads persisted notes from backend; per-note buffers handled by Editor component'). Choose B if the merge responsibility truly belongs in Editor; choose A if this hook owns the responsibility. The current state is halfway between, which is the worst place to be.

**Location:** ``frontend/src/useBootNotes.ts:51-65``

**Acceptance:**
- Either: (A) implement the merge logic described (iterate backend notes, check localStorage buffers per note, apply merge strategy), or (B) simplify the JSDoc to match the implementation ('loads persisted notes from backend; per-note buffers handled by Editor component'). Choose B if the merge responsibility truly belongs in Editor; choose A if this hook owns the responsibility. The current state is halfway between, which is the worst place to be.
