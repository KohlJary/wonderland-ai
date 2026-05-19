## Ticket 034: Display tags grouped in note list view

**GUID:** 01KRXX3SA1BRDRD799772ZAZC3
**Sources:** kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 0.5-1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: add-tag-schema-and-crud-endpoints
- Soft: —

**Description:**

In the note list view, render tags for each note as small badges or labels. Optionally group notes by tag if Kohl's workflow benefits from that view (low scope here; full tag-based filtering is fast-follow).

**Acceptance:**
- Note list renders tag badges for each note
- Tags are visually distinct from note title/preview
- Clicking a tag does not filter (that's fast-follow); tags are display-only at v1

**Risk:**

Low. If grouping by tag becomes part of v1 acceptance, expand to 1.5 days.
