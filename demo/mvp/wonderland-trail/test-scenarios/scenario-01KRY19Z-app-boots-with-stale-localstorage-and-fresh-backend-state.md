## Scenario 275: App boots with stale localStorage and fresh backend state

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GF
**Severity:** silent-wrongness

**Setup:**

User had the editor open, typed a note title 'Async Patterns', but didn't save. localStorage has {title: 'Async Patterns', body: '', tags: []}. User closes browser without saving. Later, opens the app again. Meanwhile, on backend, no note with that title exists (it was never saved). NoteList will show the current persisted notes, but Editor will restore the stale draft.

**Trigger:**

App boots. Editor component mounts and restores from localStorage (title: 'Async Patterns'). User sees an editor with 'Async Patterns' in the title field.

**Expected:**

If the user intends to save this note, they should be able to. But the contract says localStorage is cleared on page reload if it's older than the server's saved version. In this case, there's no saved version to compare against (it's a new note). The expected behavior is: Editor restores the draft, shows it clearly as a draft (not a saved note), and the user can either save it or discard it.

**Concern:**

The current Editor component restores from localStorage silently. There's no indicator that this is an unsaved draft from a prior session, vs. a note being actively edited. For a new note (no noteId), the user might not realize they're recovering a draft they abandoned. If they click Save without reviewing, they might create a note they forgot they started. This is not a breakage, but it's a UX gap that could lead to accidental persistence of forgotten drafts.

**Property:**

For all notes stored in localStorage (whether new or existing), the app must indicate to the user that this is unsaved state from a prior session, with the option to keep or discard it. Unclear whether the contract intends this as a visual indicator or a confirmation dialog.

**Implies:**
- Implies missing persona or UX clarification: Kohl expects to recover unsaved drafts, but does she want a warning for each recovery, or silent restore? — flag for Alice.
- Implies contract gap: contract-note-002 doesn't specify the UX for draft recovery (banner, dialog, badge, etc.). Need UI spec.
