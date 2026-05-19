## Scenario 193: Kohl clicks on a search result and the note opens in the editor

**GUID:** 01KRXYDGJMBMVN3X0NM5ETQ1NW
**Severity:** silent-wrongness

**Setup:**

Kohl has searched for 'experiment' and 8 results are displayed. She is reading the previews, looking for a specific note.

**Trigger:**

Kohl clicks on one of the search results (e.g., the third result, 'Experiment 3: Rust async').

**Expected:**

The search view closes or transitions to the editor view. The note's full content (title and body) loads in the editor. The editor's title input shows 'Experiment 3: Rust async' and the body shows the full note text. Kohl can now read, edit, or save the note.

**Concern:**

If clicking a result doesn't navigate to the note, Kohl can view search results but cannot act on them — the search feature is incomplete. If the wrong note opens, Kohl gets lost or frustrated.

**Property:**

search-result-click-must-navigate-to-and-load-the-correct-note

**Implies:**
- frontend-must-thread-selected-note-id-from-search-click-to-editor-initialization
