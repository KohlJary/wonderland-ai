## Ticket 071: Tag input component (frontend editor UI)

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2H
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-tag-input
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: tag-note-association-frontend
- Blocked by: —
- Soft: —

**Description:**

Add tag input field to the note editor. Support comma-separated or space-separated tag entry. Validate tag names (alphanumeric + dash only, max 20 chars per tag). Show user's existing tags as autocomplete options. No backend calls yet — this is UI only.

**Acceptance:**
- Tag input field is present in editor
- Tags can be entered and parsed
- Validation rejects invalid tags and surfaces errors
- Autocomplete shows existing tags

**Risk:**

Low. This is straightforward React component work.
