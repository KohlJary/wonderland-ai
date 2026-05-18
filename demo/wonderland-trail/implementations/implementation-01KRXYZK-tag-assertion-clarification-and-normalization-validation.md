## Implementation 046: Tag assertion clarification and normalization validation

**GUID:** 01KRXYZK62C2W4KWYRZERKDDHQ
**Side:** backend
**Ticket:** test-assertions-lack-clarity-no-failure-message-overly-permissive-logic
**Contract:** contract-note-01KRXYD0 (tag-name-normalization-and-validation-semantics) + contract-note-tag-case-sensitivity (agreed: case-sensitive, v1)
**Ready for review:** yes

**Approach:**

Added _normalize_and_validate_tag_names() helper that strips leading/trailing whitespace and rejects (HTTP 400) empty/whitespace-only tags. This is called from all tag endpoints. Updated test assertions from permissive (accepting multiple outcomes) to explicit (exact expectations with clear failure messages). Also added _escape_like_pattern() for SQL LIKE wildcard escaping in search.

**Files:**
- src/backend/api/notes.py: Added _normalize_and_validate_tag_names() and _escape_like_pattern(); updated _associate_tags(), associate_tag(), and search_notes(); comprehensive docstrings with contract references
- src/backend/models.py: Updated Tag docstring with case-sensitivity invariant documentation
- tests/test_tag_scenarios.py: Fixed 3 test assertions to be explicit and non-permissive with clear failure messages; updated docstrings
