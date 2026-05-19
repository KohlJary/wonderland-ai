## Implementation 038: Wire Search result click navigation to editor

**GUID:** 01KRXYNMX3MHQE5GY5YDKEVMQX
**Side:** frontend
**Ticket:** kohl-searches-notes-by-title-and-body-content
**Contract:** search-endpoint-contract-get-api-search-with-pagination/v1
**Ready for review:** yes

**Approach:**

Added onViewNote={handleEditNote} to Search component in App.tsx. This completes the feature integration: users can now click search results to navigate to the editor and load the clicked note for viewing/editing.

**Client State:**

Search component continues to manage its own state (searchQuery, selectedTags, page, results). App-level state (view, selectedNoteId) coordinates navigation.

**Files:**
- frontend/src/App.tsx: App component now passes handleEditNote callback to Search component as onViewNote prop

**Open Questions for Pair:**
- Contract review: does the search endpoint behavior match expectations from testing? Any edge cases observed in backend that frontend should handle differently?
