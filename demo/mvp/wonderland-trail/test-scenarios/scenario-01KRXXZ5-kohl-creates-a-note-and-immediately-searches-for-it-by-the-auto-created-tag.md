## Scenario 175: Kohl creates a note and immediately searches for it by the auto-created tag

**GUID:** 01KRXXZ5QRD8WJ7NFN2AZWEHX1
**Severity:** degradation

**Setup:**

Kohl is in the editor pane with title='Research Notes' and body='Initial thoughts on quantum computing', and she types a new tag 'quantum' into the tag input field (not yet saved).

**Trigger:**

Kohl clicks Save. The Editor sends POST /api/notes with {title: 'Research Notes', body: '...', tag_names: ['quantum']}. The response includes {id: 3, tags: [{id: 44, name: 'quantum'}, ...]}. Kohl then switches to Search view and submits a search query with tags=['quantum'].

**Expected:**

The search results display the newly created note with the 'quantum' tag visible. Response time for the search is <500ms (acceptable latency).

**Concern:**

If the tag auto-creation failed silently (the tag was not actually created during POST), the search would return no results and Kohl would think her note was not saved. Or if there's a cache delay before the tag becomes visible in search, Kohl sees empty results when she searches immediately after save—a degradation in user confidence.

**Property:**

Tag auto-creation is immediate and visible in downstream searches

**Implies:**
- tag-auto-create-during-post
- tag-visible-in-search-immediately-after-save
- low-latency-search-after-tag-creation
