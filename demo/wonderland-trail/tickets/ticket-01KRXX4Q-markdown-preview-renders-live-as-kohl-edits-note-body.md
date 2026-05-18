## Ticket 048: Markdown preview renders live as Kohl edits note body

**GUID:** 01KRXX4Q2MWWCSCN46PBKVYSR6
**Sources:** kohl-views-markdown-rendered-notes, kohl-recalls-a-past-note-faster-via-search-than-her-old-scattered-files-workflow
**Owner:** either
**Tier:** v1
**Stack span:** full-stack
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5–2.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: kohl-creates-and-saves-experimental-notes-with-markdown-bodies
- Soft: —

**Description:**

Kohl writes markdown in the note editor's body field and sees formatted output (headers, code blocks, lists, links, images, blockquotes) rendered in real-time in a preview pane or split view. No save-to-see-preview roundtrip. localStorage persistence from prior ticket ensures edits survive reload.

**Acceptance:**
- Markdown preview component renders headers, bold, italic, code, code blocks, lists, links, images, blockquotes correctly from markdown source
- Preview pane updates synchronously as Kohl types in the body field (no debounce lag perceived as blocking)
- Preview persists across reload (consumed from prior ticket's localStorage)

**Risk:**

Markdown library choice (e.g., remark vs marked vs markdown-it) may require evaluation; pick one early. Live rendering performance may degrade on large notes — use debounce or virtual scrolling if needed. Image rendering may require CORS handling if external URLs are allowed.
