## Story 008: Markdown preview pane with live rendering

**GUID:** 01KRXRESM8FPT4WS5G1GDZ6QKN

**Persona:** developer (Kohl's UI runtime)

**Situation:**

Kohl is typing markdown in the editor pane. But she can't see how it will render — there's no preview. She needs a side-by-side split where the right pane shows live HTML rendering of the markdown she's typed.

**Need:**

As a developer building Kohl's UI, I need a React component that renders markdown in real-time as the editor's body field changes, so Kohl can see headers, code blocks, lists, links, images, blockquotes as she types.

**Acceptance:**
- Preview component is a React component that takes markdown body as a prop
- Preview renders HTML output for all core markdown features: headers (# ## ###), code blocks (```), unordered and ordered lists, links [text](url), images ![alt](url), blockquotes (>), inline code (`backtick`), bold (**text**), italic (*text*)
- Preview updates in real-time whenever the editor body prop changes (no lag)
- An inline code block does not break the layout (overflow is handled, code scrolls or wraps)
- A long code block (10+ lines) is readable (line numbers optional, but readable is required)
- Links render as clickable <a> tags; images render as <img> tags
- The preview pane is visually distinct from the editor pane (side-by-side layout is clear)

**Tier:** core

**Confusion-flags:**
- Should I use a markdown library (react-markdown, marked, markdown-it) or roll custom HTML generation? I'm assuming a library (react-markdown is idiomatic), but that's an architecture call.
- Should the preview be scrollable independently, or should both panes scroll together? I'm leaning toward independent — editor on left, preview on right, each scrolls on its own content height.
- Is the visual styling of the preview pane in scope, or is 'readable' the only requirement? I'm assuming readable is the bar — the author can style later.

**Realizes requirements:**
- markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
- offline-capable-app-with-client-side-markdown-rendering
