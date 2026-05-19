## Implementation 009: Tag input and association in the editor

**GUID:** 01KRXTHWM5AFATWW02H3Y4019E
**Side:** frontend
**Ticket:** frontend-tag-input-and-association-in-the-editor
**Contract:** POST /api/notes accepts tag_names: string[] (optional, defaults to []). Implemented per contract-note-01KRXRTT and notes-endpoint spec in src/backend/api/notes.py.
**Ready for review:** yes

**Approach:**

Created TagInput component with text input + Add button, rendered tags as removable chips below the input. Integrated into Editor.tsx: tags captured in state, persisted to localStorage alongside title/body, included in POST /api/notes payload (tag_names array). Empty and duplicate tags rejected client-side. Tags cleared on successful save.

**UI States Implemented:**
- empty: no tags added yet (input visible, no chips)
- pending: tags being accumulated (chips displayed as they are added)
- saved: success message displayed, tag list cleared

**Client State:**

Tags live in Editor state (EditorState.tags: string[]). Restored from localStorage on mount, persisted on every keystroke (add/remove tag). Cleared after successful POST. Single source of truth in component state; no sync issues with backend until POST succeeds. Frontend state is ephemeral (client-side only) until save.

**Files:**
- frontend/src/TagInput.tsx: new file, TagInput component with input+button, chip rendering, add/remove handlers
- frontend/src/Editor.tsx: added tags to EditorState, added handleTagsChange, updated localStorage restore/persist to include tags, updated POST payload to include tag_names array, integrated <TagInput/> into render

**Known Limitations:**
- No autocomplete from existing tags (deferred to v2 per ticket description)
- Tags stored only in client state + localStorage until POST succeeds; no pre-save persistence
- No tag search or dropdown selection; v1 is simple text-input-and-add
