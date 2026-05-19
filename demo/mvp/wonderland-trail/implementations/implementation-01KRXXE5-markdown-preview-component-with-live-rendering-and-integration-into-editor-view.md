## Implementation 029: Markdown preview component with live rendering and integration into editor view

**GUID:** 01KRXXE5HZF29WE23ASWQ365RV
**Side:** frontend
**Ticket:** ticket-01KRXX3X, ticket-01KRXX3X (Build markdown preview component + Integrate into editor view)
**Contract:** pure client-side rendering — no server contract. Editor contract unchanged: POST /api/notes {title, body, tag_names} → {id, title, body, tag_names, tag_ids, created_at, updated_at}. Preview is internal React state plumbing (body string flows from Editor textarea through EditorLayout callback to Preview component).
**Ready for review:** yes

**Approach:**

Preview component takes raw markdown body as prop and renders formatted HTML. EditorLayout wires Editor and Preview side-by-side; Editor emits body changes via onBodyChange callback; Preview receives body as prop and re-renders on every change using React.useMemo for performance. DOMPurify sanitizes all HTML before rendering to prevent XSS. Marked library handles markdown parsing with default options (no configuration needed for v1). Editor remains fully functional independent of Preview (Preview is optional layer).

**UI States Implemented:**
- loading: Editor disables form during POST /api/notes; Preview remains visible and responsive
- empty: Editor empty, Preview renders empty div (no error or placeholder)
- error-recoverable: Editor shows error message from save failure; Preview continues to render unsaved edits
- success: Editor shows 'Saved' message with Note ID; Preview still visible with last-saved content
- preview: Preview pane updates immediately as user types in Editor (core feature of EditorLayout)

**Client State:**

No new client state for Preview. EditorLayout manages previewBody state (string): Editor.onBodyChange → setPreviewBody → Preview.body prop. State is ephemeral (React state, not localStorage). Canonical body state is the Editor textarea value + localStorage keystroke buffer (Editor's responsibility). Preview is read-only; preview state is derived from Editor, not stored independently.

**Files:**
- frontend/src/Preview.tsx: renders markdown HTML with DOMPurify sanitization; handles parse errors gracefully
- frontend/src/EditorLayout.tsx: wires Editor (left) + Preview (right) side-by-side with 50/50 split
- frontend/src/Editor.tsx: already calls onBodyChange on every keystroke (no changes needed; integration already in place)
- frontend/package.json: marked + dompurify already listed as dependencies (confirmed in place)

**Open Questions for Pair:**
- No backend seam — this is pure frontend. But confirm: should Preview pane display the note ID or confirmation message after Editor successfully saves? Currently EditorLayout doesn't show the saved note ID in Preview; only Editor shows it. Is this UX correct or should Preview show post-save state?

**Known Limitations:**
- Syntax highlighting for code blocks: code blocks render but without language-specific syntax coloring (deferred to v2)
- Mobile layout: Preview + Editor split is fixed 50/50 desktop split; mobile stacked layout deferred (v2)
- Editing existing notes: feature creates new notes only; cannot fetch + edit existing note by ID (out of scope for Feature 004)
- Preview overflow: very long notes (10k+ characters) render without virtualization; performance acceptable for v1 scope but may need optimization for e.g., 100k+ character documents
