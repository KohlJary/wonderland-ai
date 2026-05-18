## Implementation 045: Test assertion clarity for tag deduplication

**GUID:** 01KRXYZ5PHRW3TQ57QHPRB0DAP
**Side:** backend
**Ticket:** ticket-01KRXY8N7JPKPYA5B89Q37ZNYW
**Contract:** Tag deduplication is case-sensitive and exact-match (no fuzzy matching). Per contract-note-01KRXYD0 and _normalize_and_validate_tag_names() implementation.
**Ready for review:** yes

**Approach:**

The backend _normalize_and_validate_tag_names() function already deduplicates tags by exact string match (case-sensitive). Updated the corresponding test to assert exactly 2 unique tags with clear failure message per ticket's request.

**Invariants Enforced:**
- Tag names within a single note request are deduplicated by exact string match (case-sensitive)
- Duplicate tags are removed at request validation time, not at database insertion

**Schema Changes:**

No schema changes (validation only)

**Failure Modes Handled:**
- Duplicate tag names in request: silently deduplicated at validation boundary

**Files:**
- tests/test_notes_edge_cases.py: test_post_note_with_duplicate_tag_names_in_list now asserts specific behavior (2 tags) with clear failure message
