## Ticket 081: Backend: revision_id computation happens on every GET, creating redundant hashing

**GUID:** 01KRY1M30C2XWQSWS392YTD52F
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup
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

From review ``feature-009-kohl-drafts-and-saves-experimental-notes-with-persistent-backup`` (change-required):

**Concern:** This is a performance issue in a read-heavy system. If there are 100 notes and Kohl loads the notes list, the server computes 100 SHA256 hashes. If she then opens a note in the editor, that's another hash computation. Most production systems would cache the revision_id in the database so it can be returned without recomputation. However, for the MVP scope (single-user, small dataset), this is acceptable performance-wise. The real concern is maintainability: if revision_id ever needs to change (e.g., to include additional state in the hash), every endpoint needs to be updated. The code duplication (compute_revision_id calls spread across multiple endpoints) makes this fragile.

**Request:** Consider caching revision_id as a database column (computed on every write, cached on reads). For now, this is acceptable, but document it. Add a comment on compute_revision_id(): '// TODO: cache in database to avoid recomputation on every GET. For MVP, recomputation is acceptable; revisit after performance testing.' This flags the tradeoff for future readers.

**Location:** ``src/backend/api/notes.py:372-378, 413-430``

**Acceptance:**
- Consider caching revision_id as a database column (computed on every write, cached on reads). For now, this is acceptable, but document it. Add a comment on compute_revision_id(): '// TODO: cache in database to avoid recomputation on every GET. For MVP, recomputation is acceptable; revisit after performance testing.' This flags the tradeoff for future readers.
