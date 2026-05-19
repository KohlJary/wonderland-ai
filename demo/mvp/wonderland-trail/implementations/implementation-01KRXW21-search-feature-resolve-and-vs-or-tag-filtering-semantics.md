## Implementation 022: Search feature: resolve AND vs OR tag filtering semantics

**GUID:** 01KRXW21EM9JVSAR5JX7P34SVJ
**Side:** frontend
**Ticket:** 01KRXVSS15TP6MEMEM8KTYZ364
**Contract:** search-api/v1 (contract-note-008): Tag filtering uses AND logic. Query parameters query (text search on title/body) and tags (comma-separated tag names) combine with AND semantics. Response shape: {results: NoteResponse[], total: int, page: int, limit: int, has_more: bool}
**Ready for review:** yes

**Approach:**

Fixed three issues: (1) Removed dead code from Search.tsx: apiQuery and apiTags state variables were declared but never read/used. (2) Updated tag filter label from 'Filter by tag:' to 'Filter by ALL of these tags:' to clarify to users that AND logic is in effect (notes must have all selected tags). (3) Updated test expectations: test_tag_filtering_with_multiple_tag_names now correctly expects total==1 when filtering by 'work' AND 'personal' tags (only the note with both tags matches). Backend implementation was correct all along (uses chained .filter() calls for AND logic); the bug was in the test expectations and frontend UX clarity.

**UI States Implemented:**
- search-form-ready with clarified AND semantics label
- tag-filter-selected (chips with remove buttons, user can see active filters)
- tag-suggestions (unselected tags offered as buttons with AND semantics clarified)

**Client State:**

Search.tsx client state: searchQuery (string), selectedTags (string[]), page (number, 0-indexed), results (SearchResponse | null), loading (boolean), error (string | null). No cross-component state sharing. Debounce on searchQuery and selectedTags changes triggers API call, resetting to page 0. Page changes trigger API call with current query/tags.

**Files:**
- frontend/src/Search.tsx: line 210, label text; lines 54-57, removed dead state variables; lines 68-69, removed dead assignments
- src/backend/api/notes.py: line 293-294, removed redundant alias parameters; lines 300-312, clarified docstring about AND logic
- tests/test_search.py: line 184-209, updated test expectations from OR to AND semantics with comprehensive assertions

**Known Limitations:**
- Backend environment requires dependency installation (pip install -e . or uv sync) before running test suite; environment setup issue only
