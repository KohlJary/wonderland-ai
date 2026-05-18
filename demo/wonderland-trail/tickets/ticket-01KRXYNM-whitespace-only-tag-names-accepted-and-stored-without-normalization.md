## Ticket 055: Whitespace-only tag names accepted and stored without normalization

**GUID:** 01KRXYNMY2AYJXXN7Z41P1RNSJ
**Sources:** kohl-searches-notes-by-title-and-body-content, search-wildcard-escaping-tag-validation
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

From review ``search-wildcard-escaping-tag-validation`` (change-required):

**Concern:** Whitespace-only tags are not useful and create confusing UI. If a user accidentally includes '  ' in the tag_names array, it becomes a valid tag distinct from other tags.

**Request:** Normalize tag names before storing: strip leading/trailing whitespace and skip empty strings after stripping. Add this to _associate_tags: `tag_name = tag_name.strip()` and `if not tag_name: continue`. Also add a Pydantic validator to TagCreate and NoteCreate models to reject whitespace-only tag names at the request boundary.

**Location:** ``src/backend/api/notes.py:135-160``

**Acceptance:**
- Normalize tag names before storing: strip leading/trailing whitespace and skip empty strings after stripping. Add this to _associate_tags: `tag_name = tag_name.strip()` and `if not tag_name: continue`. Also add a Pydantic validator to TagCreate and NoteCreate models to reject whitespace-only tag names at the request boundary.
