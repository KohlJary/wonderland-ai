## Implementation 027: Search component contract alignment: parameter names, response field names, pagination indexing

**GUID:** 01KRXWBFW3Z8TFRJ1M9W3QMV9M
**Side:** frontend
**Ticket:** ticket-01KRXW5Q7WXPHEFBXH9WTZPJRW (Query parameter name: contract says 'q', implementation says 'query')
**Contract:** contract-note-008 (search-api/v1): GET /api/search?q=<str>&tags=<comma-sep>&page=<int>&page_size=<int> returns {results: [{id, title, body_preview (150 chars), tag_names, tag_ids, created_at, updated_at}], total_results, page (1-indexed), page_size, has_more}
**Ready for review:** yes

**Approach:**

Updated Search.tsx component to use 1-indexed pagination (page starts at 1, not 0), use body_preview from server instead of client-side truncation, and reference correct response field names (total_results, page_size). All API calls now match contract-note-008 parameter names and response shape.

**Files:**
- frontend/src/api.ts: Updated docstring to cite contract-note-008
- frontend/src/Search.tsx: Changed initial page state to 1 (1-indexed), updated debounce reset to page 1, fixed renderNoteResult to use body_preview, updated pagination controls for 1-indexed pages, updated field references (total → total_results, limit → page_size), updated docstrings

**Open Questions for Pair:**
- Contract is fully aligned per contract-note-008. No open questions.

**Known Limitations:**
- Search results display only body_preview (150 chars) due to payload optimization. Full note content requires opening the note in editor (separate workflow).
