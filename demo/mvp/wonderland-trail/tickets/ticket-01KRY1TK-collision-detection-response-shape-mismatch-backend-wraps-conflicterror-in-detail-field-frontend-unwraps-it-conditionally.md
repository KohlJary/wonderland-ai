## Ticket 082: Collision detection response shape mismatch: backend wraps ConflictError in 'detail' field, frontend unwraps it conditionally

**GUID:** 01KRY1TK92XDMFTPQT9TY8KC4H
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

From review ``kohl-drafts-and-saves-experimental-notes-with-persistent-backup-cross-ticket-coherence-and-implementation-review`` (block):

**Concern:** The contract-note-01KRY0B8 names the expected response as {error, message, server_revision_id, server_state}, but does not explicitly document that FastAPI wraps this in a 'detail' field. The frontend's defensive unpacking is correct but suggests the contract is unclear. Additionally, the fallback path that throws if the shape doesn't match means the contract is enforced at runtime in the client rather than documented explicitly. A caller who doesn't know about FastAPI's detail wrapping will receive a cryptic error.

**Request:** Update contract-note-01KRY0B8 to explicitly state: 'HTTP 409 response body is {detail: {error: "ConflictError", message: ..., server_revision_id: ..., server_state: ...}}. FastAPI wraps the HTTPException detail in a top-level detail field. Client must unwrap before parsing.' Remove the fallback throw in api.ts and replace with an assertion, since the contract is now explicit. If the contract says 'detail', expect 'detail'.

**Location:** ``frontend/src/api.ts:128-145``

**Acceptance:**
- Update contract-note-01KRY0B8 to explicitly state: 'HTTP 409 response body is {detail: {error: "ConflictError", message: ..., server_revision_id: ..., server_state: ...}}. FastAPI wraps the HTTPException detail in a top-level detail field. Client must unwrap before parsing.' Remove the fallback throw in api.ts and replace with an assertion, since the contract is now explicit. If the contract says 'detail', expect 'detail'.
