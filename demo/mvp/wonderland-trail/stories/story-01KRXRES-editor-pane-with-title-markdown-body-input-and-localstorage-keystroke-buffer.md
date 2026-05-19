## Story 007: Editor pane with title + markdown body input and localStorage keystroke buffer

**GUID:** 01KRXRESM8FPT4WS5G1GDZ6QKM

**Persona:** developer (Kohl's UI runtime)

**Situation:**

The frontend has a placeholder App.tsx that fetches from the message endpoint. But Kohl needs an editor pane where she can type a note title and markdown body. The typed content must survive page reload by being buffered in localStorage — so if her laptop crashes mid-session, she doesn't lose her work.

**Need:**

As a developer building Kohl's UI, I need a React component that accepts note title and body input, auto-saves keystroke state to localStorage, and restores the draft on page load so Kohl's work is never lost.

**Acceptance:**
- Editor component renders two input/textarea fields: one for title, one for markdown body
- Every keystroke in either field updates localStorage.setItem('noteraft', {title, body}) in real-time or on a debounce
- On page load, the component checks localStorage and restores the draft into the input fields
- If localStorage is empty, the fields start blank
- A clear/discard button wipes localStorage and empties the fields
- The draft persists across page reloads and browser restart (localStorage lifecycle)

**Tier:** core

**Confusion-flags:**
- Should the localStorage key be 'noteDraft' singular (one active draft) or 'noteDrafts' plural keyed by note id (multiple drafts)? I'm assuming singular for now — Kohl is working on one note at a time.
- Should the debounce be implicit (save on every keystroke) or explicit (only save when user pauses)? I'm assuming every keystroke for safety, but that might be chatty — the author should decide.
- Is localStorage the right persistence layer for v1, or should this write to the backend immediately? The milestone says 'no backend writes required', so localStorage is right, but that means offline editing works but the backend is always stale until the user explicitly saves.

**Realizes requirements:**
- offline-capable-app-with-client-side-markdown-rendering
- core-crud-operations-create-edit-delete-notes-with-markdown-bodies-and-optional-tags
