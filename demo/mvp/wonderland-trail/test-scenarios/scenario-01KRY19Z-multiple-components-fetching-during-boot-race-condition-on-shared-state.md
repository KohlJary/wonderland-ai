## Scenario 278: Multiple components fetching during boot: race condition on shared state

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GJ
**Severity:** curiosity

**Setup:**

App.tsx mounts. Both Editor (if noteId is null) and NoteList (mounted in the render) have useEffect hooks that fetch data. Editor fetches localStorage OR tries to fetch a specific note. NoteList fetches all notes. Both fire simultaneously (or nearly so) during app boot.

**Trigger:**

App initializes; both Editor and NoteList useEffect hooks execute on the same tick.

**Expected:**

Both fetches complete independently. Editor state is set from localStorage or a note-fetch. NoteList state is set from a notes-fetch. No conflicts, because they're writing to different React state variables.

**Concern:**

This is not a bug, but it's a coupling point. If, in future, the app needs to coordinate between Editor and NoteList (e.g., 'clear Editor and NoteList if a delete operation succeeds'), the independent fetch pattern will make coordination harder. For v1, this is fine. But the pattern is worth documenting to avoid future entanglement.

**Property:**

Each component's initialization should be independent and side-effect-free with respect to other components. If component A's state changes, component B's state should not be invalidated unless component B explicitly subscribes to A's changes.

**Implies:**
- Implies architectural decision: should there be an app-level state manager (Context, Redux, etc.) that coordinates Editor and NoteList initialization, or is component-local state acceptable? — future consideration, not blocking for v1.
