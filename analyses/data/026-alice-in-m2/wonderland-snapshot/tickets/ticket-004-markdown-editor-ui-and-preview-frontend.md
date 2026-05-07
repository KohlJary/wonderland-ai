## Ticket 004: Markdown editor UI and preview (frontend)

**Sources:** write-and-publish-my-homepage-in-markdown
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1.5–2.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: public-homepage-viewing
- Blocked by: markdown-publishing-setup
- Soft: —

**Description:**

Frontend editor: User sees a split-pane interface (edit on left, live preview on right). User types markdown; preview updates in real-time. Publish button POSTs content to backend. On success, show 'Published!' confirmation and display the shareable URL. No autosave in v1. Form validation: reject empty content, warn on unsaved changes.

**Acceptance:**
- User sees split-pane editor (input + preview)
- Preview updates on keystroke
- Publish button submits to backend and shows result (success/error)
- User sees their shareable URL after publish
- Unsaved-changes warning appears on page exit if content is modified

**Risk:**

Real-time markdown preview performance; may need debouncing. Live preview library choice (e.g., remark, markdown-it with client-side renderer).
