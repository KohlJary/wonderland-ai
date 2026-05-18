## Ticket 083: Editor.tsx conflict state initialization ambiguity: two distinct conflict states (conflict vs conflictState) manage overlapping concerns

**GUID:** 01KRY1TK9JZY4ZTMJTMKGZGTCK
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, kohl-drafts-and-saves-experimental-notes-with-persistent-backup-cross-ticket-coherence-and-implementation-review
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

From review ``kohl-drafts-and-saves-experimental-notes-with-persistent-backup-cross-ticket-coherence-and-implementation-review`` (change-required):

**Concern:** Having two state variables with overlapping type and similar naming creates confusion about which conflict has been detected and what the user sees. Reading the flow: (1) on mount, if both server and buffer exist and buffer is newer, set `conflict` and show merge UI; (2) if user saves and gets 409, set `conflictState` and show modal. The invariant that only one can be active is implicit. If both become true simultaneously (race condition on save during mount reconciliation), the UI will render both, which is undefined behavior. The naming doesn't distinguish 'boot-time' from 'save-time' conflict.

**Request:** Rename the state variables to make their role explicit: `bootConflict` (for boot-time merge detection) and `saveConflict` (for save-time collision). Add an assertion or guard that prevents both from being true simultaneously. Alternatively, unify into a single state variable with a type discriminant: `const [conflict, setConflict] = useState<{type: 'boot', ...} | {type: 'save', ...} | null>(null)`. The current structure is correct in behavior but confusing in intent.

**Location:** ``frontend/src/Editor.tsx:54-56``

**Acceptance:**
- Rename the state variables to make their role explicit: `bootConflict` (for boot-time merge detection) and `saveConflict` (for save-time collision). Add an assertion or guard that prevents both from being true simultaneously. Alternatively, unify into a single state variable with a type discriminant: `const [conflict, setConflict] = useState<{type: 'boot', ...} | {type: 'save', ...} | null>(null)`. The current structure is correct in behavior but confusing in intent.
