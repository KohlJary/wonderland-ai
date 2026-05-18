## Scenario 206: Empty search query or all-whitespace query is handled without error

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHM
**Severity:** degradation

**Setup:**

Kohl opens the search view. The search input is empty (user hasn't typed anything yet).

**Trigger:**

User submits search (if search is button-based) or waits for debounce (if keystroke-based).

**Expected:**

Either: (a) no results are shown, with a helpful message like 'Enter a search term to find notes', or (b) all notes are listed as a default view (if search is optional).

**Concern:**

If the client sends a request to /api/search?q= (empty), the backend might return all notes (full-text index match-all behavior) or error. Frontend might display 'No results found' when Kohl hasn't actually searched yet, creating confusion. Alternatively, if the client silently does nothing, Kohl might wonder if the search feature is broken.

**Property:**

For all empty or whitespace-only search queries, the UI provides clear, non-error feedback to Kohl (either 'please enter a search term' or 'showing all notes' depending on the intended behavior).

**Implies:**
- Implies contract: Backend should either (a) reject empty queries with 400, or (b) return all notes without error. Frontend should handle both gracefully. Clarify the contract.
