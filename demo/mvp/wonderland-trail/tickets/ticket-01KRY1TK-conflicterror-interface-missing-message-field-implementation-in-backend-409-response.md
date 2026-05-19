## Ticket 084: ConflictError interface missing 'message' field implementation in backend 409 response

**GUID:** 01KRY1TKA0P8F25E5QNZ6WDJXT
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

**Concern:** On careful reading, the backend does include the message field, so this is not a breaking mismatch. However, the frontend's fallback in updateNote() (line 138) provides a default if message is missing: `message: conflictData.message || 'Conflict detected'`. This suggests the interface declared message as required but the implementation treats it as optional. This inconsistency is a minor contract fragility.

**Request:** Make the message field explicitly required in the contract-note and ensure the backend always populates it (which it does). No code change needed since both sides are aligned, but update the contract-note-01KRY0B8 to state: 'message field is always present and human-readable (e.g., "Note has been updated since you last synced...").' Remove the `|| 'Conflict detected'` fallback in api.ts since the contract guarantees message is present.

**Location:** ``frontend/src/api.ts:68-72``

**Acceptance:**
- Make the message field explicitly required in the contract-note and ensure the backend always populates it (which it does). No code change needed since both sides are aligned, but update the contract-note-01KRY0B8 to state: 'message field is always present and human-readable (e.g., "Note has been updated since you last synced...").' Remove the `|| 'Conflict detected'` fallback in api.ts since the contract guarantees message is present.
