## Scenario 280: Concurrent tabs with different localStorage: only one backend note exists

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GM
**Severity:** curiosity

**Setup:**

User has two browser tabs open, both with the app. Tab A is editing note 42, with a draft in localStorage. Tab B is editing a new note, with a different draft in localStorage (no id yet). Both tabs reload at roughly the same time. Backend has note 42 and no other notes. Both tabs fetch GET /notes and get note 42.

**Trigger:**

Tab A merges its localStorage draft with note 42 from the backend. Tab B merges its localStorage draft (new note, no id) with the backend list (which has note 42).

**Expected:**

Tab A correctly hydrates note 42, seeing its local draft is stale or in sync. Tab B should realize its draft is a new note (no matching id in backend), and either restore it as a new unsaved note, or discard it. Both tabs should eventually show the same persisted state (note 42), but each might have different unsaved drafts. This is fine for v1 (no cross-tab sync).

**Concern:**

Currently, Editor component doesn't do any merge logic based on revision_id. It just restores from localStorage for a new note, or fetches a note by id. If the user opens the same note in two tabs and both have local drafts, they'll both try to save independently, and one will overwrite the other (or trigger a conflict, if revision_id checking is implemented). For load-on-boot, the main concern is: does the merge logic correctly distinguish between 'draft for an existing note' and 'draft for a new note'? If noteId is null but localStorage has an id, what happens?

**Property:**

On app boot in each tab, the merge logic must distinguish: (1) Draft for an existing note (localStorage.id exists, matches a backend note id), (2) Draft for a new note (localStorage.id is null or doesn't match any backend note), (3) and handle each case independently per tab (no cross-tab sync in v1).

**Implies:**
- Implies potential issue: if localStorage.id is non-null but doesn't match any backend note (orphaned draft), the current Editor logic will try to fetch by id, get a 404, and show an error. The draft will be preserved in localStorage but not shown to the user. This is a UX gap.
