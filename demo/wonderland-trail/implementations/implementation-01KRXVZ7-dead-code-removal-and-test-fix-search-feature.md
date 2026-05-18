## Implementation 020: Dead code removal and test fix: search feature

**GUID:** 01KRXVZ79EDXK709734EFAVDJB
**Side:** frontend
**Ticket:** ticket-01KRXVSS194TZEX5V93PA99V11
**Contract:** search-api/v1 (GET /api/search with AND tag filtering per contract-note-008)
**Ready for review:** yes

**Approach:**

Removed unused state variables apiQuery and apiTags from Search.tsx component. These were initialized but never read, suggesting incomplete refactoring. Also fixed test_tag_filtering_with_multiple_tag_names in test_search.py to correctly expect AND semantics (only notes with ALL specified tags) rather than OR semantics.

**Client State:**

Removed apiQuery and apiTags which were declared but never used. Kept searchQuery, selectedTags, page, results, loading, error which are all actively used.

**Files:**
- frontend/src/Search.tsx: removed unused state declarations lines 54-55 and assignments lines 68-69
- tests/test_search.py: updated test_tag_filtering_with_multiple_tag_names to expect data["total"] == 1 (only 'Both tagged' note), matching implemented AND logic
