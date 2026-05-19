## Implementation 021: Search feature: frontend cleanup and backend docstring clarification

**GUID:** 01KRXW1SMHH5X98E7GGXM66E0G
**Side:** frontend
**Ticket:** ticket-01KRXRQZ
**Contract:** search-api/v1 per contract-note-008: GET /api/search?query=q&tags=tag1,tag2&page=page&limit=limit returns paginated SearchResponse with AND logic for tag filtering
**Ready for review:** yes

**Approach:**

Removed unused apiQuery and apiTags state variables from Search component that were tracking API parameters but never read. These were likely from an earlier implementation pattern that changed. Backend search_notes function already implements AND logic correctly via chained .filter() calls; removed redundant alias parameters and clarified docstrings to match the corrected test expectations.

**Client State:**

Search component state now only tracks: searchQuery, selectedTags, page, limit, results, loading, error. Removed redundant tracking of what was sent to API (the current values are the source of truth).

**Files:**
- frontend/src/Search.tsx: removed unused state (apiQuery, apiTags) and their assignments
- src/backend/api/notes.py: removed redundant alias parameters from Query definitions, clarified docstring
