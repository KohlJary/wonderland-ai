## Scenario 245: Kohl edits a note, closes the app, opens it again — localStorage data loads instantly, then a backend sync merges any server changes

**GUID:** 01KRY18F88GKW92A57SY2C1JVQ
**Severity:** degradation

**Setup:**

Kohl has previously saved a note to the backend with revisionId 'rev-3'. She opens the app and sees the title and body loaded from localStorage (which still has her last edited state). The backend also has the note with revisionId 'rev-3'.

**Trigger:**

Kohl opens the app. The editor populates from localStorage immediately (instant render). Then, in the background, a 'load on boot' API call fetches the note from the backend.

**Expected:**

The editor renders Kohl's localStorage state instantly so she can keep working without waiting. After the background load completes, if the backend revisionId matches localStorage's revisionId, nothing changes. If they differ (another tab saved a change), the app shows a merge UI or warning instead of silently overwriting.

**Concern:**

If the app waits for the backend load before showing the editor, Kohl sees a blank screen for 500ms–1s even though her work is sitting in localStorage. Degradation: the app works correctly but feels slow. Conversely, if the merge strategy is wrong, Kohl's work from one tab silently clobbers changes from another tab.

**Property:**

localStorage loads synchronously; backend merge is async and safe
