## Review 013: Frontend Editor, Preview, TagInput components and API client

**GUID:** 01KRXTQXF3CSZYHASMK802XGFM
**Files reviewed:** frontend/src/Editor.tsx, frontend/src/Preview.tsx, frontend/src/TagInput.tsx, frontend/src/EditorLayout.tsx, frontend/src/api.ts, frontend/src/App.tsx, frontend/package.json
**Verdict:** request-changes

### Findings

#### change-required: Editor and Preview export both default and named exports; EditorLayout uses defaults inconsistently
**Location:** frontend/src/Editor.tsx:249, frontend/src/Preview.tsx:54, frontend/src/EditorLayout.tsx:14-15
**Quote:**

```
export default Editor;
// and at the top of EditorLayout.tsx:
import Editor from './Editor';
```

**Read:** Editor.tsx and Preview.tsx each export both `export function Editor(...)` and `export default Editor;`. EditorLayout.tsx imports both as defaults (`import Editor from './Editor'`). This works, but the codebase convention is unclear: is the primary interface default or named?
**Concern:** Mixed export patterns are a clarity hazard. A reader has to check each file to understand the import/export convention. This is especially problematic when a team grows or code is maintained over time. The convention should be consistent across all components.
**Request:** Pick one convention and apply it uniformly. Recommended: named exports for all components. Change Editor.tsx to `export { Editor };` (remove default export). Update EditorLayout.tsx to `import { Editor } from './Editor';`. Do the same for Preview and TagInput. This makes it clear that components are primarily imported by name, not as defaults. Alternatively, if you prefer defaults, remove the named exports and require default imports everywhere.

#### change-required: Preview error handling is silent; user may not realize markdown parsing failed
**Location:** frontend/src/Preview.tsx:33-38
**Quote:**

```
try {
      const rawHtml = marked(body);
      const cleanHtml = DOMPurify.sanitize(rawHtml);
      return cleanHtml;
    } catch (err) {
      // Malformed markdown: show error inline, not as crash
      console.error('Markdown parse error:', err);
      return `<p style="color: #999; font-style: italic;">Error parsing markdown</p>`;
    }
```

**Read:** When marked() throws, the error is logged to console (developer-only) and a gray message is rendered. The user sees 'Error parsing markdown' in the preview pane, but there's no alert, toast, or visual prominence. The Editor doesn't know the preview failed and doesn't prevent save.
**Concern:** A user might write markdown with syntax issues, see the gray message, and either ignore it or not notice it. Then they save, the backend accepts the partial markdown that marked() successfully parsed, and the user's intent is lost. The console log is useless for end users. The error message is too subtle.
**Request:** Two approaches: (A) Communicate the error to the parent: add an `onPreviewError?: (error: string) => void` prop to Preview. In EditorLayout, call this and update the Editor's error state. (B) If Preview is standalone, make the error message prominent: red background, bold text, 'Preview Error: <detail>'. The goal is to ensure the user notices and can decide whether to save or fix the markdown.

#### suggestion: TagInput accepts tag names longer than backend constraint without warning
**Location:** frontend/src/TagInput.tsx:19-35
**Quote:**

```
const handleAddTag = () => {
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }
    // Avoid duplicates
    if (tags.includes(trimmed)) {
      setInput('');
      return;
    }
    onTagsChange([...tags, trimmed]);
    setInput('');
  };
```

**Read:** TagInput validates for empty tags and duplicates but not length. The backend enforces `tag_name: str = Field(min_length=1, max_length=100)`. If the user pastes a 150-character string, TagInput accepts it, displays it as a chip, and then the backend rejects it on save with a 422 error.
**Concern:** Poor user experience: the tag appears valid in the UI, then save fails with a cryptic Pydantic validation error. The user doesn't know why their tag was rejected.
**Request:** Add client-side validation: `if (trimmed.length > 100) { setError('Tag name too long (max 100 characters)'); return; }`. Show an error message (inline or toast) instead of silently rejecting. This prevents the tag from being added and informs the user why.

#### suggestion: Editor sends defensive || '' for body, masking state invariant
**Location:** frontend/src/Editor.tsx:116-120
**Quote:**

```
const payload: NoteCreateRequest = {
        title: state.title,
        body: state.body || '',
        tag_names: state.tags,
      };
```

**Read:** The Editor constructs a payload with `body: state.body || ''`. This is defensive: if state.body is falsy (empty string, null, undefined), use ''. But state.body is always a string (initialized as '' in EditorState and only updated via handleBodyChange). The || '' guard is unnecessary.
**Concern:** The guard implies uncertainty about the state invariant. Future developers might assume state.body can be null and add defensive code elsewhere, compounding the issue. It's a small thing, but it signals that the author wasn't confident the invariant would hold.
**Request:** Remove the || ''. Change to `body: state.body`. If you're concerned about the invariant breaking in the future, add a comment: `// state.body is always a string; see EditorState initialization and handleBodyChange`. This makes it clear: the invariant is deliberate, not accidental.

#### note: Editor keystroke buffering to localStorage is well-designed
**Location:** frontend/src/Editor.tsx:35-98
**Quote:**

```
const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTitle = e.target.value;
    setState({ ...state, title: newTitle });
    saveToLocalStorage({ ...state, title: newTitle });
  };
  const handleBodyChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newBody = e.target.value;
    setState({ ...state, body: newBody });
    saveToLocalStorage({ ...state, body: newBody });
  };
  const handleTagsChange = (newTags: string[]) => {
    setState({ ...state, tags: newTags });
    saveToLocalStorage({ ...state, tags: newTags });
  };
```

**Read:** The Editor restores from localStorage on mount (with error handling), writes on every keystroke, and clears after successful save. The three handlers (title, body, tags) are consistent and clear. The pattern is solid.
**Concern:** No issues with this implementation.
**Request:** No change requested.

#### note: api.ts interface types align with backend contract
**Location:** frontend/src/api.ts:1-40
**Quote:**

```
export interface Note {
  id: number;
  title: string;
  body: string;
  tag_names: string[];
  created_at: string;
  updated_at: string;
}

export interface NoteCreateRequest {
  title: string;
  body?: string;
  tag_names?: string[];
}

export interface NoteUpdateRequest {
  title?: string;
  body?: string;
  tag_names?: string[];
}
```

**Read:** The TypeScript interfaces (Note, NoteCreateRequest, NoteUpdateRequest, NoteResponse) match the backend Pydantic schemas. The contract is documented at the top. The fetch functions are consistent: error handling includes res.text() for detail, status codes are checked.
**Concern:** No issues observed.
**Request:** No change requested.

### Approvals

- Editor component handles all three state updates (title, body, tags) with clear, consistent handlers. Persistence to localStorage on every keystroke and restoration on mount is correct.
- Preview uses marked for parsing and DOMPurify for sanitization, which is the right defense against XSS.
- TagInput is clean: add by button or Enter, remove by × button, no duplicates allowed.
- App.tsx correctly wires Editor as the main export.
- All component prop types are defined clearly (EditorProps with optional onBodyChange, PreviewProps, TagInputProps).
- api.ts exports clear TypeScript interfaces for all request/response shapes. Fetch functions handle errors and include detail messages.

### Cross-domain references

- The TagInput tag length constraint (max 100 chars) should match the backend. If the backend constraint changes, the frontend validation must change too. Consider documenting this contract in a shared constants file (e.g., config.ts or contracts.ts) so the constraint is defined once.
- The Preview error handling might need to signal upward to the Editor. Flag for the Hatter: are there markdown parsing edge cases we should test?
- The markdown rendering (marked) and sanitization (DOMPurify) are well-chosen, but if the backend ever needs to parse or validate markdown, ensure it uses the same library/rules. Mismatches can lead to XSS if the frontend sanitizes differently than the backend.
