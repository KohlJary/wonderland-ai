## Implementation: Editor state revision_id invariant defensive documentation

**Ticket:** 01KRY1M2 (editor-state-initialization-creates-implicit-contract-with-revision-id)
**Story:** feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup
**Contract:** contract-note-01KRXXCX-multi-tab-collision-detection-revision-id-versioning (revision_id field semantics)

**Approach:**
Added a defensive multi-line comment in the EditorState interface clarifying the revision_id invariant. The comment explains:
- When revision_id is null (new notes, stale buffers from localStorage)
- When revision_id is set (on successful save responses from server)
- When revision_id is cleared (on conflict, because buffer is uncommitted)
- The key invariant: trust server responses, be skeptical of localStorage buffers
- Why: localStorage buffers may have stale revision_id if the note was edited elsewhere

This is not a behavioral change; it's defensive documentation that prevents future readers from trusting stale revision_id values from localStorage.

**Files Touched:**
- frontend/src/Editor.tsx: enhanced comment on EditorState.revision_id field (lines 38-44)

**Contract Assumptions:**
- revision_id is an opaque string returned by the server in POST/PUT/GET responses
- localStorage buffer may persist stale revision_id if the note was edited elsewhere
- On conflict (409), the server returns the current revision_id; client should update to this server version
- Client should not trust revision_id from localStorage if there's any doubt about staleness

**Known Limitations:**
- This is documentation only; no runtime behavior change
- The comment does not prevent the code from accidentally using stale revision_id, but it makes the risk visible to future readers
- Defensive validation (e.g., checking revision_id freshness against server on mount) is out of scope for this ticket

**UI States Implemented:**
- N/A (documentation change)

**Client State:**
- No change to state management; revision_id continues to live in EditorState.revision_id
- The comment clarifies the invariant without changing how it's used

**Open Questions for Pair:**
- None; this is purely frontend-side documentation in response to Caterpillar review

**Ready for Review:**
true
