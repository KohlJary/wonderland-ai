## Story 002: Markdown preview renderer component

**GUID:** 01KRXRDES1D2YNVMG16Y6PFVSB

**Persona:** Dev integrating live preview — needs a reusable React component for rendering markdown

**Situation:**

Editor pane receives markdown input. A preview pane on the right must render the markdown in real-time as the user types, showing headers, code blocks, lists, links, images, and blockquotes.

**Need:**

As a developer shipping the editor UI, I want a markdown-to-HTML renderer React component that consumes markdown text and emits rendered HTML, so that the preview pane can display live feedback without round-tripping to the backend.

**Acceptance:**
- Preview component renders headers (# ## ###) correctly
- Code blocks (``` syntax) render with proper formatting (monospace, distinct background)
- Ordered and unordered lists render correctly
- Links and images render with href and src attributes
- Blockquotes render with distinct styling
- Rendering is real-time — no visible lag as the user types in the editor

**Tier:** core

**Confusion-flags:**
- Which markdown library should we use? react-markdown, markdown-it, marked, remark? This is an architectural choice that should be made in M2 — not blocking the story, but it needs resolution before implementation.
- Inline code (backticks) and bold/italic are mentioned in the operator's done_when as implicit in a 'markdown library's baseline' — assuming the chosen library handles these by default.
- Should the preview component handle XSS risk? Markdown libraries typically sanitize HTML, but we should confirm this is a non-issue before shipping.

**Realizes requirements:**
- offline-capable-app-with-client-side-markdown-rendering
- markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
