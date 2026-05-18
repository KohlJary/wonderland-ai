## Ticket 080: Backend 409 response structure in frontend doesn't handle parsed error response correctly

**GUID:** 01KRY1M2ZZ0CX2H5BA6VAT8MM5
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

**Concern:** The code assumes the 409 response has the shape `{ error, server_revision_id, server_state }` (per the ConflictError interface in api.ts), but the backend returns `{ error, message, server_revision_id, server_state }` (see src/backend/api/notes.py:389-395). The extra `message` field is harmless, but the code should be explicit about what structure it expects. If the backend response changes, the code will silently use wrong data.

**Request:** Make the conflict error response structure explicit. In api.ts, define the expected response shape as a type and parse it before returning. Example: `type ConflictResponse = { error: string; message: string; server_revision_id: string; server_state: Note }; const conflictData: ConflictResponse = await res.json(); return { conflict: conflictData };`. This ensures the response is validated at the API boundary, not in the component.

**Location:** ``frontend/src/Editor.tsx:306-318``

**Acceptance:**
- Make the conflict error response structure explicit. In api.ts, define the expected response shape as a type and parse it before returning. Example: `type ConflictResponse = { error: string; message: string; server_revision_id: string; server_state: Note }; const conflictData: ConflictResponse = await res.json(); return { conflict: conflictData };`. This ensures the response is validated at the API boundary, not in the component.
