## Implementation 032: NoteList component and app navigation for notes view

**GUID:** 01KRXY8N66Y1JY4DHWB4AXM20V
**Side:** frontend
**Ticket:** display-tags-grouped-in-note-list-view
**Contract:** GET /api/notes returns Note[] (contract-note-01KRXRTT) with shape {id, title, body, tag_names: string[], tag_ids: number[], created_at, updated_at}. NoteList consumes tag_names for display; tag_ids are present in response for future use (filtering). Response is reverse-chronological (newest first) — NoteList displays in received order.
**Ready for review:** yes

**Approach:**

Created NoteList component that fetches all notes via GET /api/notes, displays each note with title, body preview (first 150 chars), tags as styled badges, and creation date. Integrated into App.tsx as third navigation view. Handles UI states: loading spinner, error-recoverable with retry, empty state, and results grid (responsive auto-fill layout). Tags render as small rounded badges with light blue background and blue border; clicking a note triggers onEdit callback (wired for future editing feature).

**UI States Implemented:**
- loading: centered spinner text 'Loading notes…' while fetching from /api/notes
- error-recoverable: error message with Retry button; calls window.location.reload() on retry
- empty: centered message 'No notes yet. Start by creating your first note in the editor.' when list is empty and loading is complete
- results: note cards in CSS Grid (auto-fill, minmax 300px), each showing title (blue, bold), body preview, tag badges (if present), creation date (gray)

**Client State:**

None persisted beyond the current session. Component fetches fresh list on mount via useEffect. Notes array held in local React state (setNotes). Loading and error states are local (setLoading, setError). On unmount or rerender, state is not cached. User navigates back to editor and returns to list to refresh.

**Files:**
- frontend/src/NoteList.tsx: new component (252 lines) with fetching logic, UI state machine (loading/error/empty/results), tag badge rendering, note cards in responsive grid, CSS styling with hover effects
- frontend/src/App.tsx: added NoteList import, expanded view type to include 'list', added Notes navigation button, updated main render to show list view

**Known Limitations:**
- onNoteClick callback defined but click-to-edit feature not yet wired to load note into editor (Editor component doesn't yet support loading a note by id from the server — future ticket)
- Tag clicking does not filter notes (display-only in v1, as per ticket acceptance criteria)
