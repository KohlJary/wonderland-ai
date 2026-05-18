## Story 005: Editor UI layout — two-pane with title, body editor, and tags

**GUID:** 01KRXRDES1D2YNVMG16Y6PFVSE

**Persona:** Dev building the editor interface — needs a React component structure for the main note-taking experience

**Situation:**

Kohl opens the notebook and sees an editor pane on the left (title + body markdown input) and a preview pane on the right (live rendered HTML). She can also add tags. The layout is responsive and usable on a laptop screen.

**Need:**

As a frontend developer, I want a two-pane editor layout component that hosts the title input, markdown body textarea, tag input, and a side-by-side preview, so that the capture experience is organized and Kohl can write and preview simultaneously.

**Acceptance:**
- Title input field is visible and editable at the top
- Markdown body textarea occupies the main left pane
- Tag input area is below the body (or integrated nearby)
- Preview pane renders on the right side of the screen (or below on mobile)
- Layout scales responsively (full-width on mobile, side-by-side on desktop)
- No backend calls required — everything uses localStorage and client-side state

**Tier:** core

**Confusion-flags:**
- Should this story include buttons for Save, Delete, New Note? M1's done_when focuses on 'keystroke resilience' (localStorage) and 'preview rendering,' not multi-note navigation. Defer Save/Delete buttons to M1.5 or M2; this story owns the layout skeleton.
- Should the editor support undo/redo? Not in scope for M1; localStorage provides the recovery path (reload the page).
- This story is about the editor component structure; the specific CSS styling and typography are secondary. A functional, readable layout is the acceptance bar.

**Realizes requirements:**
- offline-capable-app-with-client-side-markdown-rendering
- markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
- single-operator-notebook-with-no-authentication-or-setup
