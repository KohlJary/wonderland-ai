## Ticket 033: Add tag inputs to editor UI

**GUID:** 01KRXX3SA1BRDRD799772ZAZC2
**Sources:** kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1-1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: add-tag-schema-and-crud-endpoints
- Soft: —

**Description:**

Add a tag input field to the note editor (either dropdown multiselect from existing tags or free-text input that creates/adds tags on save). Show selected tags as chips/badges. Persist tag selections to localStorage alongside note body so work survives reload.

**Acceptance:**
- Editor displays a tag input field below or alongside title/body inputs
- User can select or add tags (interaction style TBD by Tweedledee per contract negotiation)
- Selected tags display as visual chips
- Tag selections persist to localStorage with note data
- Tag selections survive page reload
- On save, selected tags are sent to backend via POST /notes/{id}/tags

**Risk:**

Interaction pattern (dropdown vs. free-text vs. hybrid) may require iteration with Kohl persona; expand if UX feedback arrives mid-ticket.
