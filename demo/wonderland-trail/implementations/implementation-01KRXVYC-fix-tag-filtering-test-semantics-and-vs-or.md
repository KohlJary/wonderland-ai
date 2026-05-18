## Implementation 019: Fix tag filtering test semantics (AND vs OR)

**GUID:** 01KRXVYC6D3A9E566B7CQNSCPF
**Side:** frontend
**Ticket:** 01KRXVSS15TP6MEMEM8KTYZ364
**Contract:** GET /api/search tag filtering uses AND semantics: notes matching tags=work,personal must have BOTH 'work' AND 'personal' tags. Per api/notes.py search_notes() docstring.
**Ready for review:** yes

**Approach:**

Updated test_tag_filtering_with_multiple_tag_names() to expect AND semantics (all tags must match) rather than OR (any tag matches). The implementation uses SQLAlchemy filter() in a loop, which constrains each iteration, resulting in AND logic. The docstring at src/backend/api/notes.py line 267-268 explicitly confirms AND semantics. Test now creates notes with 'work' only, 'personal' only, and both tags; filters for tags=work,personal; and asserts total=1 (only the 'both tagged' note matches).

**Client State:**

N/A — this is a test fix, not a UI implementation

**Files:**
- tests/test_search.py: updated test_tag_filtering_with_multiple_tag_names() docstring and assertion from OR to AND semantics
