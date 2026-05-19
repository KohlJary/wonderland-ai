## Ticket 041: Frontend: Markdown preview pane with live rendering from body input

**GUID:** 01KRXX4GE0CW1944AM7WDJG87G
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-can-view-markdown-rendered-notes-in-both-editor-and-read-mode
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.75–1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: frontend-editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer
- Soft: —

**Description:**

Build React component that accepts body text as prop and renders it as markdown HTML. Use a markdown library (e.g., react-markdown or markdown-it). Support: headers (# ## ###), bold/italic, code blocks (triple backtick + language tag), inline code, lists (- and numbered), links, images, blockquotes. Do NOT support tables, footnotes, or other advanced features in v1. Component should update live as body text changes (prop-driven re-render). Style with basic CSS (dark or light theme TBD by design; ship with readable defaults). Place preview pane side-by-side or below editor pane (layout TBD in M3 component integration).

**Acceptance:**
- Component renders markdown body as HTML
- Headers, bold, italic, code blocks, lists, links, images, blockquotes render correctly
- Preview updates live as prop changes
- No markdown rendering errors on valid input
- Styling is readable (headers distinguish from body, code is monospace, etc.)

**Risk:**

Markdown library choice or edge-case rendering bugs could add 0.5 days. If design requests custom styling per element (e.g., specific colors for code blocks), scope to defaults for v1 and fast-follow theme customization.
