## Story 011: Developer can render markdown preview from body input with headers, code blocks, lists, links, images, blockquotes

**GUID:** 01KRXRFV251BRQPQMWQTZBXJSW

**Persona:** Dev Maya: testing the live preview logic. She writes markdown in the editor body field and watches the preview pane render it in real-time. She's verifying that the markdown parser + React rendering produces clean HTML for all the required markdown features.

**Situation:**

The editor now accepts input; Maya needs to add the preview pane. Kohl expects live markdown rendering as she types, and the requirements specify headers, code blocks, lists, links, images, blockquotes as table-stakes for v1.

**Need:**

As Maya, I want to render markdown from the body input into a preview pane, so that Kohl sees her writing rendered as HTML in real-time as she types.

**Acceptance:**
- A preview pane renders to the right of (or below) the editor body field
- When the developer types markdown in the body, the preview updates in real-time (no save button required)
- All required markdown features render: headers (# ## ###), code blocks (```), unordered and ordered lists, links ([text](url)), images (![alt](url)), blockquotes (>)
- Inline code (backticks) and basic formatting (bold, italic) are rendered
- The preview is read-only — Kohl edits in the body field, not the preview
- No errors in console when rendering complex markdown

**Tier:** core

**Confusion-flags:**
- Markdown library choice not yet made — assuming react-markdown or similar standard library. If there's a specific contract around sanitization (e.g., no script tags), that should be surfaced by the Queen.
- Image rendering: assuming images are inlined as <img> tags with relative or absolute URLs. No image upload logic in this story; Kohl provides URLs manually in the markdown.

**Realizes requirements:**
- markdown-rendering-in-a-side-by-side-preview-pane-headers-code-blocks-lists-links-images-blockquotes
- offline-capable-app-with-client-side-markdown-rendering
