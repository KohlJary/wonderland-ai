## Ticket 014: Acceptance criteria mismatch — incomplete endpoint coverage

**GUID:** 01KRXSJ9M8DPKZSEXG0NS0MA6E
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body, backend-note-and-tag-crud-endpoints
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``backend-note-and-tag-crud-endpoints`` (block):

**Concern:** The ticket's acceptance criteria explicitly name seven endpoints. Shipping only two fails the acceptance definition. A caller cannot update a note, delete a note, list all notes, or manage tags — all required by the ticket scope.

**Request:** Either: (a) implement the remaining five endpoints to meet the ticket's stated acceptance criteria, or (b) retract the ticket's overreach and file separate tickets for the missing endpoints with separate estimates. Option (a) is preferred if the estimate buffer allows; option (b) is appropriate if scope was locked and estimates don't account for all seven endpoints. Coordinate with Rabbit to clarify which path the team agreed to.

**Location:** ``src/backend/api/notes.py (full file)``

**Acceptance:**
- Either: (a) implement the remaining five endpoints to meet the ticket's stated acceptance criteria, or (b) retract the ticket's overreach and file separate tickets for the missing endpoints with separate estimates. Option (a) is preferred if the estimate buffer allows; option (b) is appropriate if scope was locked and estimates don't account for all seven endpoints. Coordinate with Rabbit to clarify which path the team agreed to.
