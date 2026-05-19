## Implementation 049: Tag name normalization and whitespace validation

**GUID:** 01KRXZ14TFZNKZFM8E3HP156WW
**Side:** backend
**Ticket:** ticket-01KRXYNM
**Contract:** contract-note-01KRXYD0/v1: tag names must be stripped, whitespace-only names rejected with 400, deduplication case-sensitive, stored normalized
**Ready for review:** yes

**Approach:**

Added _normalize_and_validate_tag_names() that enforces contract-note-01KRXYD0: strip leading/trailing whitespace, reject (400 Bad Request) any tag name that is empty or whitespace-only after stripping, deduplicate by exact match (case-sensitive). Updated _associate_tags() and associate_tag() endpoint to use this function. Updated all tag-related endpoints to normalize before lookup/create.

**Invariants Enforced:**
- Tag name after normalization is always non-empty (reject at request boundary with 400 if empty or whitespace-only)
- Tag names in responses always have whitespace stripped
- Within a single note, deduplicate by exact match (case-sensitive) — if request has [research, research], store [research]
- Search patterns escape LIKE metacharacters (%, _) to ensure they match literally, not as wildcards

**Schema Changes:**

No migrations (tag table schema unchanged; behavior is validation on write, not schema constraint)

**Failure Modes Handled:**
- User sends tag_names with whitespace only (e.g., ['  ', 'research']): reject entire request with 400 Bad Request + detail message
- User sends tag_names with leading/trailing whitespace (e.g., ['  research  ']): normalize to 'research', store normalized form
- Search query contains %, _ characters: escape them in LIKE pattern to match literally (e.g., search for '100%' matches '100%' exactly, not as a wildcard)

**Files:**
- src/backend/api/notes.py: added _normalize_and_validate_tag_names(), updated _associate_tags() and associate_tag(), updated search_notes() with LIKE escaping
- src/backend/models.py: added contract reference comment documenting case-sensitive tag names
- tests/test_tag_scenarios.py: updated test assertions to expect strict rejection/normalization
- tests/test_notes_edge_cases.py: updated test assertions for deduplication and whitespace handling

**Open Questions for Pair:**
- Contract-note-01KRXYD0 specifies rejection (400 Bad Request) for whitespace-only tags. Ticket-01KRXYNM acceptance criteria say 'skip empty strings after stripping' which could mean silent filtering. Current implementation rejects with 400 and tests enforce this. Confirm you're aligned with 400-rejection behavior, or do you want silent filtering on client-side validation instead?

**Known Limitations:**
- Tag names are case-sensitive (research, Research, RESEARCH are three distinct tags) — this is per contract, but may surprise users who expect case-insensitive dedup
