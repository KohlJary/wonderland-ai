## Ticket 038: Build markdown preview component with live rendering

**GUID:** 01KRXX3X6YM2V427JKP7R0ENYW
**Sources:** kohl-views-markdown-rendered-notes
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1–2 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: kohl-creates-and-saves-experimental-notes-with-markdown-bodies-editor-ui
- Soft: —

**Description:**

Create a React component that takes raw markdown body text as input and renders it as formatted HTML (headers, code blocks, lists, links, images, blockquotes). Component should update reactively as the body input changes. Use a lightweight markdown parser (e.g., remark or markdown-it). No server involvement — this is pure client-side rendering.

**Acceptance:**
- Markdown body text renders as formatted HTML in the preview pane
- Headers (# ## ###), bold (**text**), italic (*text*), code blocks (```), inline code (`code`), lists (- and 1.), links ([text](url)), images (![alt](url)), and blockquotes (>) all render correctly
- Preview updates immediately as user types in the body input
- Component handles edge cases: empty body, malformed markdown, very long bodies without crashing

**Risk:**

Markdown parser choice and configuration could affect performance on very large notes or cause unexpected rendering. Plan to test with 10k+ character bodies. If parser is slow, may need lazy rendering or virtualization; expand estimate to 2–3 days.
