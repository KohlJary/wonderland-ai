## Ticket 004: Edit homepage flow (form + save)

**Sources:** edit-my-homepage-in-markdown
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1-1.5 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: user-authentication-and-session-management, homepage-schema-and-markdown-parsing
- Soft: —

**Description:**

Frontend form for authenticated users to edit their homepage markdown. Textarea with submit button. On submit, POST markdown to backend. Backend validates ownership (user owns their own homepage), parses markdown, stores raw + rendered, returns success. Simple UX — no live preview, no draft versioning.

**Acceptance:**
- Authenticated user sees edit form populated with their current markdown
- User can edit textarea and submit changes
- Backend validates user ownership before accepting edit
- Successful save returns updated page preview (rendered HTML)
- User cannot edit another user's homepage

**Risk:**

Simple implementation — but ownership validation is critical; double-check this in review.
