## Implementation 057: Revision ID state tracking in Note model

**GUID:** 01KRY1EXCHZV8QPY93ZK2AT2TX
**Side:** frontend
**Ticket:** revision-id-state-tracking-in-note-model-for-collision-detection
**Contract:** GET /notes response includes revision_id (string); POST/PUT /notes request includes revision_id field (string | null); response includes updated revision_id
**Ready for review:** no

**Approach:**

Added revision_id field to Note interface (string | null). Populated when notes load from backend GET /notes response, null for new notes. Included in save request payloads, updated after successful save responses.

**Client State:**

revision_id lives in the Note state object. Sourced from backend on load (via GET /notes), null on creation. Updated after successful save (via POST/PUT response). No reconciliation needed; revision_id is read-only from the client's perspective — the backend is the source of truth.

**Files:**
- src/frontend/types/Note.ts: added revision_id: string | null to Note interface
- src/frontend/hooks/useNoteState.ts: initialize revision_id from loaded notes, null for new notes
- src/frontend/hooks/useNoteState.ts: include revision_id in save request payload
- src/frontend/hooks/useNoteState.ts: update revision_id from save response

**Open Questions for Pair:**
- What is the exact shape of the GET /notes response — is revision_id at top level or nested?
- On POST (new note creation), does the backend always return a revision_id, or can it be null?
- On PUT (update), is revision_id a separate field in the request or part of a metadata envelope?

**Known Limitations:**
- No validation of revision_id format — treated as opaque string per ticket acceptance
- Collision detection logic is in save/load tickets, not here; this ticket is state shape only
- localStorage persistence of revision_id is deferred to the load/merge ticket
