## Ticket 009: Frontend: Tag input and association in the editor

**GUID:** 01KRXRNHX5PSM0YXPN7RV91FHS
**Sources:** kohl-can-organize-notes-with-tags-and-read-them-in-markdown-preview, tag-input-and-association-in-the-editor
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: backend-note-and-tag-crud-endpoints-with-schema
- Soft: —

**Description:**

Build a TagInput component that appears below the title and body fields. Allow the user to type a tag name and press Enter (or click Add) to add it to a list. Display added tags as removable chips/badges. When the user clicks Save on the note, include the current tag list in the POST /notes or PUT /notes/:id request. After successful save, clear the tag list. Support fetching existing tags from GET /tags endpoint (fast-follow: autocomplete; v1 is list-input only).

**Acceptance:**
- TagInput component renders a text input and an 'Add' button
- User can type a tag name and press Enter or click Add to add it
- Added tags appear as removable chips below the input
- User can click an X or similar on a chip to remove it
- When Save is clicked on the note, the current tag list is sent to the backend as part of the note payload
- After successful save, the tag list is cleared
- vitest tests cover adding tags, removing tags, and Save-with-tags workflow
- Tag names are trimmed and non-empty (client-side validation)

**Risk:**

If autocomplete or tag search is requested in v1, defer to fast-follow and scope this ticket to simple text-input-and-add. If tag association UX requires a more complex design (e.g., selecting from a dropdown of existing tags), clarify in M5 contract negotiation.
