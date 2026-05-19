## Contract Note 016: Page load hydration and GET /api/notes/{id} contract

**GUID:** 01KRXXE8K06P4ZYZVKWB3NQWPV
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

n/a, fresh feature thread

**Proposed Change:**

GET /api/notes/{id} response 200: {id, title, body, tags: [{id, name}], created_at, updated_at, version}. Version field is opaque revision_id (used in PATCH If-Match header per Queen ruling-004). On 404: note does not exist. On 403: access denied.

**Source:** Your question 2 + ADR-004 (recovery across reload) + Queen ruling-004 (collision detection).

**Frontend Impact (Tweedledee):**

On mount, if URL has /editor/notes/:id, fetch GET /api/notes/{id}. If localStorage exists: compare version (if stale, show conflict warning and let user choose Keep Draft vs. Load Server). If no localStorage: hydrate editor from response. Cache version after successful PATCH so next reload detects conflicts.

**Backend Impact (Tweedledum):**

Return version field so client can compare against cached version from prior save.
