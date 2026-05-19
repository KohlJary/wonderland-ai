## Ticket 040: Frontend: Editor pane with title + markdown body input and localStorage keystroke buffer

**GUID:** 01KRXX4GE0CW1944AM7WDJG87F
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: frontend-note-list-with-search-and-tag-filter, frontend-markdown-preview-pane-with-live-rendering
- Blocked by: —
- Soft: —

**Description:**

Build React editor component with two input fields (title text input, body textarea). Wire both fields to component state. On every keystroke in either field, persist state to localStorage under 'current_note_draft'. On component mount, restore from localStorage if draft exists. Include visual indicator (e.g., 'Draft saved' or timestamp) when keystroke buffer writes to storage. Title field should be required-looking (label + clear indication); body should be optional. Do not wire to backend yet — this is frontend state only. Markdown rendering happens in a separate component.

**Acceptance:**
- Editor mounts and displays title + body input fields
- Typing in either field updates component state
- State persists to localStorage on every keystroke
- On reload, draft restores from localStorage
- Visual indicator shows when draft was last saved
- Title field is visually marked as required; body is optional

**Risk:**

If localStorage quota exceeded or storage events collide, expand to 2.5 days. If PM/design requests rich editor (Slate, Draft.js) instead of textarea, scope to textarea for v1 and fast-follow rich editor separately.
