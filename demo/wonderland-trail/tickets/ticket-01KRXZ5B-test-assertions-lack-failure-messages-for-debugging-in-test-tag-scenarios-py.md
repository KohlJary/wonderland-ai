## Ticket 057: Test assertions lack failure messages for debugging in test_tag_scenarios.py

**GUID:** 01KRXZ5BMXQQT03839QCWRZH0M
**Sources:** kohl-searches-notes-by-title-and-body-content, feature-006-kohl-searches-notes-full-stack-integration-and-contract-coherence
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

From review ``feature-006-kohl-searches-notes-full-stack-integration-and-contract-coherence`` (change-required):

**Concern:** This slows debugging. When a test fails in CI, a developer must re-run locally and add print() statements to understand what went wrong. The comparison file test_notes_edge_cases.py already includes detailed assertion messages; test_tag_scenarios.py should match that standard for consistency.

**Request:** Add failure messages to all assertions in test_tag_scenarios.py that currently lack them. Example: `assert len(note["tag_names"]) == 3, f"Expected 3 distinct tags after normalization, got {len(note['tag_names'])}: {note['tag_names']}"` and `assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, f"Expected case-sensitive distinction between research/Research/RESEARCH, got {set(note['tag_names'])}"`  Scope: ~10 minutes, mechanical. Mirrors existing style in test_notes_edge_cases.py.

**Location:** ``tests/test_tag_scenarios.py:72, 76, 91, 106 (and others)``

**Acceptance:**
- Add failure messages to all assertions in test_tag_scenarios.py that currently lack them. Example: `assert len(note["tag_names"]) == 3, f"Expected 3 distinct tags after normalization, got {len(note['tag_names'])}: {note['tag_names']}"` and `assert set(note["tag_names"]) == {"research", "Research", "RESEARCH"}, f"Expected case-sensitive distinction between research/Research/RESEARCH, got {set(note['tag_names'])}"`  Scope: ~10 minutes, mechanical. Mirrors existing style in test_notes_edge_cases.py.
