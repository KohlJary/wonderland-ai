## Scenario 161: Kohl's 'research-notes' tag renders correctly in the list even though the backend response accidentally includes a null tag_names field instead of an empty array

**GUID:** 01KRXXYBA04FZFE3AR0DTZ7BWM
**Severity:** silent-wrongness

**Setup:**

A bug in the backend (or API version mismatch) causes a note's tag_names field to be null instead of [] in the GET /api/notes response. Kohl loads the note list.

**Trigger:**

The React component attempts to map over note.tag_names to render badges.

**Expected:**

The note renders without crashing. If tag_names is null, the component treats it as 'no tags' and renders no badges (same as empty array). The note title and body preview still display correctly. Other notes in the list continue to render normally.

**Concern:**

If the component does not guard against null tag_names, the map() call will throw an error: 'Cannot read property map of null'. The note list crashes or fails to render the affected note, breaking the user experience. Kohl cannot see her other notes either (if the entire list component crashes).

**Property:**

Tag rendering is defensive against missing or malformed tag data from the backend

**Implies:**
- Component initializes tag_names defensively: const tags = note.tag_names || [] before rendering
- Or, the TypeScript interface marks tag_names as required, and the API contract enforces it (never null)
- Either way, null tag_names does not cause a crash
