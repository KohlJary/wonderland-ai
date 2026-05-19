## Ticket 039: Integrate markdown preview into the note editor view

**GUID:** 01KRXX3X6YM2V427JKP7R0ENYX
**Sources:** kohl-views-markdown-rendered-notes
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: build-markdown-preview-component-with-live-rendering
- Soft: —

**Description:**

Wire the markdown preview component into the note editor page. Display the preview pane alongside the body input field (or in a tab, depending on UX preference — defer to Alice's call on layout). Ensure preview reflects current unsaved edits. Test that preview is readable and doesn't break the editor layout on various screen sizes.

**Acceptance:**
- Preview pane is visible on the note editor page
- Preview content updates in real-time as user types
- Editor layout remains readable on desktop, tablet, and mobile
- Preview gracefully handles notes with no content (empty or whitespace)

**Risk:**

Layout conflict if the preview pane competes for space with the editor input. If screen real estate is tight on mobile, may need to switch to tab-based view (preview vs. edit toggle). Coordinate with Tweedles during M3 if layout decision needs deferral.
