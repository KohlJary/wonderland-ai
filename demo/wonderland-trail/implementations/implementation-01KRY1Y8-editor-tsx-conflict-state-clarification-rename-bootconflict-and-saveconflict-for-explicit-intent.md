## Implementation 064: Editor.tsx conflict state clarification: rename bootConflict and saveConflict for explicit intent

**GUID:** 01KRY1Y87DS2GGXF0NHFFTRF66
**Side:** frontend
**Ticket:** feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup
**Contract:** contract-note-01KRY0B8 (collision-detection-contract): Editor maintains bootConflict (boot-time merge) and saveConflict (save-time 409 collision). ConflictError response shape from PUT /notes/{id} is {detail: {error, message (required), server_revision_id, server_state}}.
**Ready for review:** yes

**Approach:**

Renamed two ConflictState variables in Editor.tsx from `conflict` and `conflictState` to `bootConflict` and `saveConflict` to explicitly document their distinct roles. Updated all 10+ call sites to use the new names and clarified comments. Strengthened type-checking in api.ts to enforce ConflictError contract (message field required). Enhanced useBootNotes.ts JSDoc to explain separation of concerns.

**UI States Implemented:**
- boot-merge: shows side-by-side comparison of unsaved buffer vs. server version on app load (early return, full-screen UI)
- save-collision: shows modal overlay when 409 response received, allowing user to choose keep-edits or load-server-version

**Client State:**

bootConflict and saveConflict are mutually exclusive: only one is active at a time. bootConflict triggers on mount if both buffer and server exist; saveConflict triggers on save attempt if 409 received. Both reset to null after user chooses keep or load. revision_id state in EditorState is separate (null for new/stale, set from server responses, reset on 409).

**Files:**
- frontend/src/Editor.tsx: renamed conflict→bootConflict and conflictState→saveConflict; updated function names and all 15+ references
- frontend/src/api.ts: added explicit 'message' field check in ConflictError type-guard; removed fallback default since contract guarantees presence
- frontend/src/useBootNotes.ts: enhanced JSDoc with detailed rationale for separation of concerns (global vs. per-note scope)

**Open Questions for Pair:**
- None currently. The conflict state naming is now unambiguous. Both boot-time merge and save-time collision flows are clearly distinguished.
