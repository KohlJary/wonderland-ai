## Scenario 201: Search returns results within 200ms even with 500+ notes in database

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHF
**Severity:** degradation

**Setup:**

Database contains 500 notes with varied content. Kohl types a common search term ('experiment'). The search endpoint is not yet indexed; substring matching is O(n).

**Trigger:**

User types query in search input field (onChange event). Client sends debounced API request to GET /api/search?q=experiment.

**Expected:**

Results appear on screen within 200ms (per ticket acceptance). Search is responsive and Kohl perceives it as instant.

**Concern:**

Without full-text indexing (FTS5), SQLite will scan every note's title + body. O(n) scan on 500 notes might exceed 200ms threshold. Kohl perceives slowness and stops trusting the search.

**Property:**

For all n >= 500, search results appear within 200ms. Response time degrades gracefully with note count (e.g., 100ms for 100 notes, 180ms for 500 notes, hitting 200ms only at extreme scale).

**Implies:**
- Implies backend decision: FTS5 full-text index should be created during migration to keep search fast. Flag for Tweedledum if this is deferred to v2.
