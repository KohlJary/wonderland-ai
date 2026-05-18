## Ticket 054: SQL LIKE wildcard metacharacters not escaped in search

**GUID:** 01KRXYNMXSDPXBXNE4YWMMH2CS
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

From review ``search-wildcard-escaping-tag-validation`` (block):

**Concern:** Silent wrongness: users get unexpected search results. A search for '100%' should find only notes containing the literal string '100%', not '100' followed by anything. This is a correctness bug that silently produces wrong data.

**Request:** Escape SQL LIKE metacharacters in the user query. Replace % with %% and _ with _% in the search pattern. Example: `search_pattern = f"%{q.replace('%', '%%').replace('_', '_')}%"`. Verify by running the existing test_search_wildcard_issues.py tests (they currently document the bug and will pass once fixed).

**Location:** ``src/backend/api/notes.py:346-350``

**Acceptance:**
- Escape SQL LIKE metacharacters in the user query. Replace % with %% and _ with _% in the search pattern. Example: `search_pattern = f"%{q.replace('%', '%%').replace('_', '_')}%"`. Verify by running the existing test_search_wildcard_issues.py tests (they currently document the bug and will pass once fixed).
