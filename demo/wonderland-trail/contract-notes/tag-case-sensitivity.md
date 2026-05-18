# Contract Note: Tag Case Sensitivity

**Slug:** tag-case-sensitivity
**Version:** v1 (agreed)
**Date agreed:** this thread
**Referenced by:** test-assertions-lack-clarity (ticket 052)

## Current Shape

Tag names are case-sensitive. A note with tags `["research", "Research", "RESEARCH"]` creates three distinct tags. Tag lookups and associations use exact string match on tag name.

## Proposed Change

N/A — this note documents the decision made on ticket 052 to resolve an ambiguous test assertion.

## Source

**Ticket 052** — "Test assertions lack clarity: no failure message, overly permissive logic"

The test `test_tag_names_case_sensitivity_deduplication` was accepting either case-sensitive (3 unique tags) or case-insensitive (1 unique tag) behavior without specifying which was correct. The review requested clarification.

## Backend Impact

**Dum decision:** Tags are case-sensitive at the database layer. The `Tag.name` column has a UNIQUE constraint and no case-folding. Lookups use exact-match (`Tag.name == tag_name`). No schema change required; this is the current implementation.

**Invariant enforced:** `Tag.name` uniqueness is case-sensitive. "research" and "Research" are distinct tags and can coexist.

**Failure modes handled:**
- User provides tags with varying case: creates multiple tags. Expected behavior per this contract.
- User expects case-insensitive dedup: they will see three tags instead of one. Documented in test.

## Frontend Impact

*Tweedledee fills in.*

**Expected frontend behavior:**
- When displaying a note's tags, all case variants are shown (if they exist).
- When searching or filtering by tag name, the search is case-sensitive: "research" will not match "Research".
- When associating a new tag via POST /api/notes/{id}/tags, the tag name is case-sensitive.

*Please confirm the frontend accepts case-sensitive tag handling, or escalate to the Cat if UX design requires case-insensitive dedup.*

## Resolution

**Status:** agreed

Tag names are case-sensitive per implementation. The test assertion now documents this specific behavior with a clear failure message. No code changes to the backend required; test was tightened to enforce the decision.

---

## Rationale

Case-sensitive tags are simpler to implement and maintain than case-insensitive dedup, which would require:
- Schema change (adding a `name_lower` column for lookups)
- Write-time normalization logic
- Index strategy changes

The current behavior is predictable and explicit. Users who need case-insensitive organization can be coached by UX; the contract is now clear.
