## Scenario 187: User is on /editor with unsaved draft, navigates to /search, back button returns to /editor — draft is lost

**GUID:** 01KRXYDBED29B1DN9NNN3336YK
**Severity:** degradation

**Setup:**

User has typed content in editor but not saved. Editor state is in React memory only. User navigates to /search. History is [/editor, /search].

**Trigger:**

User clicks back button to return to /editor from /search.

**Expected:**

URL changes to /editor. Editor component mounts. Draft is lost (component state was cleared on unmount). Ticket does not specify if draft should survive navigation.

**Concern:**

If drafts are only in React state, they will be lost on navigation away and back. If localStorage is used, drafts persist. Ticket doesn't address draft preservation — implementation must clarify and potentially add confirmation dialog.

**Property:**

If component state should survive unmounting, it must be persisted to localStorage or backend, not kept only in React memory.

**Implies:**
- Implies: Product decision: should unsaved editor drafts survive navigation away?
- Implies: If yes: use localStorage for draft persistence
- Implies: UX: should there be a confirmation dialog when leaving /editor with unsaved changes?
