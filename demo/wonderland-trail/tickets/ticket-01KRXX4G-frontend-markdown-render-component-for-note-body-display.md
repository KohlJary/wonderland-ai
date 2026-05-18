## Ticket 047: Frontend: Markdown render component for note body display

**GUID:** 01KRXX4GXRYNYAV6Y2WKPTZG5E
**Sources:** kohl-creates-and-saves-experimental-notes-with-markdown-bodies, kohl-saves-a-markdown-note-with-formatting-preserved
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: frontend-editor-component-localstorage-sync

**Description:**

Integrate a markdown-to-HTML library (e.g., markdown-it, remark, or similar) and wrap it in a React component that takes a markdown string and renders it as safe HTML. Apply basic styling (headers, code blocks, lists, blockquotes, links). Use this component to display saved notes. No live preview in the editor in v1 (that's fast-follow); just static rendering on load/view.

**Acceptance:**
- Markdown render component accepts a markdown string and returns rendered HTML
- HTML includes styled headers, code blocks, lists, blockquotes, links
- Component is used to display saved notes (when user clicks a note from list)
- Raw markdown is never shown to the user in note view (only rendered HTML)
- No XSS vulnerabilities (sanitize or use safe rendering library)

**Risk:**

Library choice: different markdown libraries have different feature sets and performance profiles. Pick one (markdown-it recommended for balance of features and speed) and ship it; we can swap later if needed. Safe rendering: ensure the library sanitizes by default or use a separate sanitizer (e.g., DOMPurify).
