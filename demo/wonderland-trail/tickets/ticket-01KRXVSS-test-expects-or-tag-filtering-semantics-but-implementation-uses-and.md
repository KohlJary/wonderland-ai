## Ticket 024: Test expects OR tag filtering semantics but implementation uses AND

**GUID:** 01KRXVSS15TP6MEMEM8KTYZ364
**Sources:** kohl-can-find-past-notes-by-title-or-content-search, search-feature-implementation-full-stack
**Owner:** tweedledee
**Tier:** v1
**Stack span:** full-stack
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``search-feature-implementation-full-stack`` (block):

**Concern:** The backend implementation uses AND semantics: notes matching `tags=work,personal` must have BOTH the 'work' tag AND the 'personal' tag. Only the third note satisfies this. The test will fail with a total of 1, not 3. This is a correctness bug that will cause the test suite to fail when run.

**Request:** Fix the test to expect AND semantics: assert data["total"] == 1 (only the 'Both tagged' note matches). Alternatively, if OR semantics are intended, fix the backend implementation to use OR logic instead of AND. The docstring at notes.py line 285 specifies AND ('all tags must match'), so the test should match the implementation and docstring.

**Location:** ``tests/test_search.py:195-210 (test_tag_filtering_with_multiple_tag_names)``

**Acceptance:**
- Fix the test to expect AND semantics: assert data["total"] == 1 (only the 'Both tagged' note matches). Alternatively, if OR semantics are intended, fix the backend implementation to use OR logic instead of AND. The docstring at notes.py line 285 specifies AND ('all tags must match'), so the test should match the implementation and docstring.
