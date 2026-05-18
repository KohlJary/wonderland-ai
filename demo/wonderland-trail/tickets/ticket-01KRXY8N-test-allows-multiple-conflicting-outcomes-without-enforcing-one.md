## Ticket 053: Test allows multiple conflicting outcomes without enforcing one

**GUID:** 01KRXY8N7V6MRBHDVCVY0HHH6E
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

**Concern:** This is the same issue as the previous finding: the test accepts multiple conflicting behaviors without deciding which is right. If normalization is correct, the test should enforce that the endpoint returns 200 and normalizes. If rejection is correct, it should enforce 422. Currently, it documents the uncertainty but doesn't validate a specific contract.

**Request:** Decide: should whitespace-only tag names be normalized (stripped) or rejected? Document the decision in a contract note (e.g., 'contract-note-tag-whitespace-handling'). Then update this test to enforce the chosen behavior exclusively. For example: `assert res.status_code == 200; note = res.json(); assert 'research' in note['tag_names']; assert '  research  ' not in note['tag_names']` (if normalization) or `assert res.status_code == 422` (if rejection).

**Location:** ``tests/test_tag_scenarios.py:145–155``

**Acceptance:**
- Decide: should whitespace-only tag names be normalized (stripped) or rejected? Document the decision in a contract note (e.g., 'contract-note-tag-whitespace-handling'). Then update this test to enforce the chosen behavior exclusively. For example: `assert res.status_code == 200; note = res.json(); assert 'research' in note['tag_names']; assert '  research  ' not in note['tag_names']` (if normalization) or `assert res.status_code == 422` (if rejection).
