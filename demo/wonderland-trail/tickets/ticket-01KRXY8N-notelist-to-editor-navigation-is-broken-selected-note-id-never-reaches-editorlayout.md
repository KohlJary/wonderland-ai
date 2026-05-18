## Ticket 049: NoteList-to-Editor navigation is broken: selected note ID never reaches EditorLayout

**GUID:** 01KRXY8N6V2ZCAA002ER9D16Q5
**Sources:** kohl-organizes-notes-with-optional-tags, feature-005-kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-005-kohl-organizes-notes-with-optional-tags`` (block):

**Concern:** The feature claim is 'Kohl adds tags to notes while editing or after creation, and can browse notes grouped by tag.' The browsing works (NoteList displays notes), but clicking a note to edit it fails silently — the user gets a blank editor instead of the selected note's content. This is a critical UX break and a blocker for the feature.

**Request:** Refactor the view state to track the selected note ID. Pass it to EditorLayout so it can load the right note on mount. One approach: `const [view, setView] = useState<'editor' | 'search' | 'list'>('editor'); const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);` then `onEdit={(id) => { setSelectedNoteId(id); setView('editor'); }}` and `{view === 'editor' && <EditorLayout noteId={selectedNoteId} onSave={() => setView('list')} />}`. The EditorLayout would need to accept an optional `noteId` prop and load that note on mount if provided.

**Location:** ``frontend/src/App.tsx:46, frontend/src/NoteList.tsx:53``

**Acceptance:**
- Refactor the view state to track the selected note ID. Pass it to EditorLayout so it can load the right note on mount. One approach: `const [view, setView] = useState<'editor' | 'search' | 'list'>('editor'); const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);` then `onEdit={(id) => { setSelectedNoteId(id); setView('editor'); }}` and `{view === 'editor' && <EditorLayout noteId={selectedNoteId} onSave={() => setView('list')} />}`. The EditorLayout would need to accept an optional `noteId` prop and load that note on mount if provided.
