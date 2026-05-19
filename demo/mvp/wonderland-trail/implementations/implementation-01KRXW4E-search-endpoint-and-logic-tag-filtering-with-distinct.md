## Implementation 024: Search endpoint AND-logic tag filtering with distinct()

**GUID:** 01KRXW4EFQNNP4E3BQEPA4PG7Y
**Side:** backend
**Ticket:** 01KRXVSVWD957YMT2Z4RX9QVDW
**Contract:** search-api/v1: GET /api/search filters by tag names with AND logic (all specified tags must be present on note)
**Ready for review:** yes

**Approach:**

Added .distinct() after chained tag filters to eliminate duplicate rows from many-to-many joins. Removed redundant alias='query' and alias='tags' from Query() parameters. Updated docstrings to clarify AND semantics ('notes matching ALL tags are returned').

**Files:**
- src/backend/api/notes.py: added .distinct() at line 344, removed redundant aliases at lines 293-294, updated docstrings for clarity
- tests/test_search.py: corrected test_tag_filtering_with_multiple_tag_names to expect total==1 (AND logic), added specific assertions on result id, title, and tag_names
