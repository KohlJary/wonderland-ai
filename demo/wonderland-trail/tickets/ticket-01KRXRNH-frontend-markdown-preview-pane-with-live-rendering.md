## Ticket 008: Frontend: Markdown preview pane with live rendering

**GUID:** 01KRXRNHX5PSM0YXPN7RV91FHR
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, markdown-preview-pane-with-live-rendering
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: frontend-editor-pane-with-title-markdown-body-input-and-localstorage-keystroke-buffer
- Soft: —

**Description:**

Build React Preview component that accepts markdown body text as prop and renders it as HTML. Support headers (# through ######), code blocks (triple backtick fenced, with syntax highlighting if available via a library like react-syntax-highlighter), unordered lists, ordered lists, links, images, and blockquotes. Wire the Preview component into the Editor layout so it renders in a split pane (left: editor, right: preview) and updates live as the user types in the body field.

**Acceptance:**
- Preview pane renders markdown body as HTML
- Supports headers (# through ######), code blocks, lists (unordered and ordered), links, images, blockquotes
- Preview updates in real-time as user types in the body field (no lag)
- Editor and Preview are laid out side-by-side (left-right split or similar responsive layout)
- Preview sanitizes HTML to prevent XSS (use a library like sanitize-html or react-markdown's built-in safety)
- vitest tests cover rendering of each markdown feature and XSS prevention

**Risk:**

Markdown library choice (react-markdown, marked, etc.) and syntax highlighter dependency. Default to react-markdown (built-in safety, minimal deps) and defer syntax highlighter library selection to M5 if needed. If layout is contentious (side-by-side vs. stacked), defer to M5 contract negotiation.
