## Scenario 182: Tag filter UI adds functionality Kohl's story never requested

**GUID:** 01KRXY8R (assigned)
**Severity:** silent-wrongness

**Setup:**

Story 'Kohl searches notes by title and body content' describes searching by text only — no mention of tag filters. Implementation adds a full tag multiselect filter UI with 'Filter by ALL of these tags' suggestions beneath the search input.

**Trigger:**

Kohl uses the search feature and sees the tag filter UI below the search input.

**Expected:**

The search UI provides exactly what the story describes: a search input for text, results display with previews, and navigation. Tag filtering is not part of this story.

**Concern:**

The implementation has gone beyond the story scope. The story is Kohl's user need; the ticket is the decomposition. When they diverge, the team ships the ticket and the story goes partially unfulfilled. Kohl has a tag filter UI she didn't ask for, adding complexity she doesn't need. This is not necessarily wrong — tag filtering is a reasonable enhancement — but it's a silent scope expansion that should have been explicit. Alice should have clarified whether tag filtering belongs in v1 or is deferred to v2.

**Property:**

The search UI implementation matches the scope described in the story 'Kohl searches notes by title and body content', not a superset of functionality.

**Implies:**

- Implies scope reconciliation needed — story says search by text; implementation adds tag filtering. Flag for Alice (product) and Rabbit (scope). Decision is theirs.
