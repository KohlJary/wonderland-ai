## Implementation 062: Frontend 409 Conflict response type-safe parsing and validation

**GUID:** 01KRY1QXNKXRN98WW336AC1GKE
**Side:** frontend
**Ticket:** feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup
**Contract:** contract-note-01KRY0B8 (collision-detection-contract): PUT /api/notes/{id} with If-Match header returns 409 Conflict with response shape {error: 'ConflictError', message: string, server_revision_id: string, server_state: Note}. Frontend validates at updateNote() API boundary and throws if shape mismatches.
**Ready for review:** yes

**Approach:**

Enhanced updateNote() in api.ts to parse and validate 409 responses with explicit type-checking at the API boundary. When the backend returns 409: (1) unwraps FastAPI's HTTPException detail field, (2) validates the response shape contains required fields (error, server_revision_id, server_state), (3) throws an error if validation fails, (4) returns a typed ConflictError object to the component. This ensures contract violations cause immediate failure in updateNote rather than silent data corruption in the Editor component.

**UI States Implemented:**
- error-unrecoverable: 409 response with If-Match mismatch displays collision modal (existing, now with type-safe parsing)
- error-unrecoverable: 409 response with unexpected structure throws error (new validation)

**Client State:**

revision_id cached in Editor state, sent as If-Match header on PUT. On 409, conflictState modal displays server_state from parsed response.

**Files:**
- frontend/src/api.ts: Updated ConflictError interface to include message field and added JSDoc clarifying contract reference. Enhanced updateNote() with runtime type-checking: unwraps responseBody.detail, validates required fields exist, throws if validation fails, returns typed ConflictError.
- frontend/src/Editor.tsx: Added multi-line comment to EditorState.revision_id documenting the invariant about trusting server-sourced revision_id and ignoring stale localStorage values.
- frontend/src/useBootNotes.ts: Removed unused LocalStorageBuffer interface and simplified comments to clarify that per-note buffer merging is Editor's responsibility.

**Open Questions for Pair:**
- Tweedledum: Is the 'message' field always populated in 409 responses, or can it be omitted? Current code defaults to 'Conflict detected' if missing.

**Known Limitations:**
- useBootNotes still does not implement per-note localStorage buffer merging (deferred per review). Per-note merging is correctly delegated to Editor, which handles it when user opens a specific note.
