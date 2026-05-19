## Implementation 041: Tag case-sensitivity decision and test clarification

**GUID:** 01KRXYVWHTZ933D6TY7YMKEF28
**Side:** backend
**Ticket:** test-assertions-lack-clarity-no-failure-message-overly-permissive-logic
**Contract:** tag-case-sensitivity: v1 (case-sensitive). Tags are case-sensitive; 'research', 'Research', 'RESEARCH' are three distinct tags. No API change required; test now documents the contract explicitly.
**Ready for review:** yes

**Approach:**

Decided that tag names are case-sensitive (current implementation behavior). Updated test_tag_names_case_sensitivity_deduplication to assert exactly 3 unique tags (not 1 or 3) with specific failure messages showing the expected tag set. Added contract note documenting the decision and rationale.

**Invariants Enforced:**
- Tag names are case-sensitive: 'research', 'Research', 'RESEARCH' are three distinct tags, not deduplicated
- Tag.name column has UNIQUE constraint and treats case variants as distinct

**Schema Changes:**

None — case-sensitive behavior is already enforced by the schema and does not require migration.

**Failure Modes Handled:**
- User provides tags with varying case (research, Research): creates 3 separate tags (expected per contract)
- User expects case-insensitive dedup: will see 3 tags instead of 1; documented in test and contract note

**Files:**
- tests/test_tag_scenarios.py: Updated test_tag_names_case_sensitivity_deduplication to assert specific behavior (3 case-sensitive tags) with clear failure messages
- src/backend/models.py: Added invariant documentation stating tag names are case-sensitive
- .wonderland/contract-notes/tag-case-sensitivity.md: Contract note documenting the case-sensitive decision, rationale, and frontend expectations

**Open Questions for Pair:**
- Do you expect the frontend to validate tag input for case sensitivity, or should we document this as a backend-enforced invariant that frontend UX must accommodate?
