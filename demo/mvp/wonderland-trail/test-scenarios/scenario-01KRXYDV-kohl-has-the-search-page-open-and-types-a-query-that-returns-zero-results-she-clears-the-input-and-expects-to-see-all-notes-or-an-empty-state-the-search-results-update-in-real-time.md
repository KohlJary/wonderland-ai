## Scenario 199: Kohl has the search page open and types a query that returns zero results. She clears the input and expects to see all notes (or an empty state). The search results update in real-time

**GUID:** 01KRXYDVNXZN8XM83A00MPY61B
**Severity:** degradation

**Setup:**

Kohl is on /search with a prior query 'nonexistent' that returned zero results. The search input shows 'nonexistent' and the results pane shows 'No notes found'

**Trigger:**

Kohl highlights the text in the search input and presses Delete, clearing the input entirely. She waits 300ms (debounce time) for the search to re-execute with an empty query

**Expected:**

The results pane updates to show either (a) all notes in the system in reverse chronological order (original behavior before any search), or (b) a neutral state ('Enter a search term to begin'). The search input is visibly empty, and the transition from 'no results' to 'all results' or 'empty state' happens within 500ms (perceived as instantaneous to Kohl)

**Concern:**

If the search endpoint does not handle empty query gracefully, the re-execution might fail with a 400 error or hang indefinitely. Kohl would see the zero-results state persist, unable to recover except by navigating away. This is a degradation: the feature still works (she can navigate to a new page), but the UX is broken (she can't easily reset the search). Alternatively, if clearing the input does not re-execute the search (due to a debounce or state bug), Kohl might believe the input is 'stuck' and take extra steps to reset

**Property:**

empty search query is handled gracefully and re-executes to show default state
