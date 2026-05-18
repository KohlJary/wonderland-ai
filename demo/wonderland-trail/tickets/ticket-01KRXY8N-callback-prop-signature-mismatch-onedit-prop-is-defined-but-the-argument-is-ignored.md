## Ticket 051: Callback prop signature mismatch: onEdit prop is defined but the argument is ignored

**GUID:** 01KRXY8N7AXYHE7JTYW45EY882
**Sources:** kohl-organizes-notes-with-optional-tags, feature-005-kohl-organizes-notes-with-optional-tags
**Owner:** tweedledee
**Tier:** v1
**Stack span:** frontend
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``feature-005-kohl-organizes-notes-with-optional-tags`` (change-required):

**Concern:** This is a contract violation. The prop's type promise is broken. The next developer reading this interface will assume they can use the noteId argument, but they won't receive it. This is misleading.

**Request:** Either (a) remove the `noteId` parameter from the onEdit prop type and revise the feature to properly thread the note ID through the state (as described in the first finding), or (b) keep the parameter and fix the calling site in App.tsx to actually use it. Option (a) is cleaner and aligns with the state refactoring needed for the first finding.

**Location:** ``frontend/src/NoteList.tsx:28``

**Acceptance:**
- Either (a) remove the `noteId` parameter from the onEdit prop type and revise the feature to properly thread the note ID through the state (as described in the first finding), or (b) keep the parameter and fix the calling site in App.tsx to actually use it. Option (a) is cleaner and aligns with the state refactoring needed for the first finding.
