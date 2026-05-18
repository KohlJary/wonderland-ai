## Contract Note 023: HTTP 409 Conflict response structure: explicit documentation of FastAPI detail wrapping

**GUID:** 01KRY1WRDMHR8WGXE2NHFNAR01
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Contract-note-01KRY0B8 specifies 409 response body as {error: 'ConflictError', server_revision_id, server_state}. However, this does not document that FastAPI wraps HTTPException.detail in a top-level 'detail' field.

**Proposed Change:**

Update contract-note-01KRY0B8 to explicitly state: 'HTTP 409 Conflict response body structure: FastAPI wraps the HTTPException detail in a top-level detail field. The complete response body sent to the client is: {detail: {error: "ConflictError", message: string, server_revision_id: string, server_state: Note}}. Frontend must unwrap the detail field before parsing the ConflictError object. This is part of FastAPI's standard error handling; do not rely on unwrapped responses.'

**Source:** Caterpillar review-01KRY1TK (block finding: 'Collision detection response shape mismatch: backend wraps ConflictError in detail field, frontend unwraps it conditionally'). The frontend code currently has a fallback path that tries to parse both wrapped and unwrapped responses, which suggests contract uncertainty.

**Frontend Impact (Tweedledee):**

Once this contract is explicit, the frontend can remove defensive unpacking logic and replace it with an assertion. Instead of 'const conflictData = responseBody.detail || responseBody', the code becomes an assertion: 'const conflictData = responseBody.detail; if (!conflictData) throw new Error(...)'. This makes the contract enforced at the API boundary, not silently papered over with fallback logic.

**Backend Impact (Tweedledum):**

Backend confirms that PUT /api/notes/{id} returns HTTP 409 with FastAPI's standard detail wrapping. The exception is raised as HTTPException(status_code=409, detail={error: 'ConflictError', message: ..., server_revision_id: ..., server_state: ...}). FastAPI automatically wraps this into {detail: {...}} in the response body. No code change needed; this is documentation of existing behavior.
