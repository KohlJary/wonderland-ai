## Ticket 056: _escape_like_pattern() escape-parameter contract is implicit, not enforced

**GUID:** 01KRXZ5BMKWH1BJK76S0SSS944
**Sources:** kohl-searches-notes-by-title-and-body-content, feature-006-kohl-searches-notes-full-stack-integration-and-contract-coherence
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** required
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-006-kohl-searches-notes-full-stack-integration-and-contract-coherence`` (block):

**Concern:** If a future developer calls ilike() with the result of _escape_like_pattern() but forgets to include escape="\\" in the ilike() call, the escaping silently fails and % or _ in user input will be treated as wildcards. This is a correctness bug waiting to happen. The contract between _escape_like_pattern() and its callers is unwritten and fragile.

**Request:** Add a runtime assertion or guard to enforce the escape-parameter contract. The cleanest approach: add a docstring note to _escape_like_pattern() stating "CRITICAL: Pattern returned from this function MUST be used with ilike(..., escape='\\\\') or escaping will be ineffective. Failure to include the escape parameter is a security issue." Alternatively, if ilike() is called in more than two places, consider wrapping ilike() in a helper function that enforces escape="\\" at the call site. For v1, a clear docstring is sufficient.

**Location:** ``src/backend/api/notes.py:133-145``

**Acceptance:**
- Add a runtime assertion or guard to enforce the escape-parameter contract. The cleanest approach: add a docstring note to _escape_like_pattern() stating "CRITICAL: Pattern returned from this function MUST be used with ilike(..., escape='\\\\') or escaping will be ineffective. Failure to include the escape parameter is a security issue." Alternatively, if ilike() is called in more than two places, consider wrapping ilike() in a helper function that enforces escape="\\" at the call site. For v1, a clear docstring is sufficient.
