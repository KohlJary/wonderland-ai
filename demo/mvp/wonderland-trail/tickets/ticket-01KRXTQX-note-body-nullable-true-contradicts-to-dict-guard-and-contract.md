## Ticket 020: Note.body nullable=True contradicts to_dict() guard and contract

**GUID:** 01KRXTQXFK6YKX3NRHDBS5KMGJ
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, backend-note-crud-endpoints-models-and-database
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``backend-note-crud-endpoints-models-and-database`` (change-required):

**Concern:** This creates a category of bug that is easy to miss: code that reads note.body directly (outside to_dict()) will encounter None values unpredictably. The contract says body is always a string, and the frontend treats it as such. The schema should enforce this, not leave it to chance. The guard in to_dict() is a symptom that the invariant is not enforced at the right layer.

**Request:** Change to `nullable=False, default=""`. This makes the database enforce the invariant that body is always a string. If existing code expects to read NULL from the body column, that code is wrong and should be fixed.

**Location:** ``src/backend/models.py:54``

**Acceptance:**
- Change to `nullable=False, default=""`. This makes the database enforce the invariant that body is always a string. If existing code expects to read NULL from the body column, that code is wrong and should be fixed.
