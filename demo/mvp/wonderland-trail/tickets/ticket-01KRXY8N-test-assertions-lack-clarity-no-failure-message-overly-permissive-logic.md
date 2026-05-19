## Ticket 052: Test assertions lack clarity: no failure message, overly permissive logic

**GUID:** 01KRXY8N7JPKPYA5B89Q37ZNYW
**Sources:** kohl-organizes-notes-with-optional-tags, feature-005-kohl-organizes-notes-with-optional-tags
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

From review ``feature-005-kohl-organizes-notes-with-optional-tags`` (change-required):

**Concern:** A test that passes for multiple conflicting outcomes is not a test — it's a comment pretending to be a test. If the behavior drifts from 3 unique tags to 1 (or vice versa), this test will never catch it because it accepts both. If this is documenting an uncertain behavior, it should be marked as skipped with a `pytest.mark.skip` note about what decision is needed, not shipped as a passing test.

**Request:** Decide: are tag names case-sensitive or case-insensitive? Once decided, assert the specific behavior. For example, if case-sensitive is correct: `assert len(set(note['tag_names'])) == 3, f'Expected 3 unique tags (case-sensitive), got {len(set(note["tag_names"]))}. Tag names: {note["tag_names"]}'`. If the decision is pending, mark the test `@pytest.mark.skip(reason='Case sensitivity decision pending; see ticket #XYZ')` and document the pending decision in a contract note.

**Location:** ``tests/test_tag_scenarios.py:40–45``

**Acceptance:**
- Decide: are tag names case-sensitive or case-insensitive? Once decided, assert the specific behavior. For example, if case-sensitive is correct: `assert len(set(note['tag_names'])) == 3, f'Expected 3 unique tags (case-sensitive), got {len(set(note["tag_names"]))}. Tag names: {note["tag_names"]}'`. If the decision is pending, mark the test `@pytest.mark.skip(reason='Case sensitivity decision pending; see ticket #XYZ')` and document the pending decision in a contract note.
