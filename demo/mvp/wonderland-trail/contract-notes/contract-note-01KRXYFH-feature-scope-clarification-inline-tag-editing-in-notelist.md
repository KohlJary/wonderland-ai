## Contract Note 020: Feature scope clarification: inline tag editing in NoteList

**GUID:** 01KRXYFHHMYJQ0C88J61Z7F0G8
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Feature 005 acceptance criteria: 'Kohl adds tags to notes while editing or after creation.' Current implementation: tags can be added/edited via EditorLayout (open note → edit title/body/tags → save). Tags display in NoteList as read-only badges with no add/remove UI. Caterpillar's review raises question: does 'after creation' include inline tag editing in NoteList (add/remove tags directly in the list without opening editor), or is tag editing only via the editor?

**Proposed Change:**

Clarify feature scope for v1: Two binding options: (a) **Editor-only v1:** Tag editing only via EditorLayout (click note → edit → save). NoteList displays tags read-only. Scope is clear and implementable immediately. Inline tag editing deferred to v1.5 or v2. (b) **Inline editing v1:** NoteList includes add/remove tag UI (inline edits or modal) so Kohl can tag notes without opening the editor. Scope expands by ~2-3 days of frontend work. Alice (product owner) and Rabbit (Scrum) own this decision—it affects Feature 005's acceptance definition. The current implementation is editor-only; if inline editing is required for v1, a new ticket should be filed with updated estimates.

**Source:** Caterpillar review 01KRXY7M ('Outstanding scope question (not a blocker)'). Tweedledee's comment in implementation-01KRXCZG clarifies current state: 'Feature 005 core use case (click list → edit → add tags → save) now works end-to-end.' This implies editor-only for v1. Confirmatory ask: is this intentional or an oversight?

**Frontend Impact (Tweedledee):**

If option (a) editor-only: no change. If option (b) inline editing: add tag add/remove UI to NoteList item component. Implementation depends on interaction pattern (modal, inline chips with delete buttons, etc.). UX decision for Alice.

**Backend Impact (Tweedledum):**

No backend change required for either option. The PUT /api/notes/{id} endpoint already supports full tag updates (tag_names field). If inline editing is added in frontend, it would call PUT with updated tag_names; backend handles it the same way as editor-driven updates.
