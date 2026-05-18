## Scenario 185: User types search query 'rust' and navigates pages, then reloads (F5), search input is cleared

**GUID:** 01KRXYDBED29B1DN9NNN3336YH
**Severity:** degradation

**Setup:**

User typed 'rust' in search input, results displayed, user viewing page 2 with tag filter. URL is /search (no query params). Only React component state holds the query.

**Trigger:**

User presses F5 to reload page.

**Expected:**

Page reloads to /search. Search input is empty. Results are cleared. This is expected if URL params are not used. (If search persistence on reload is required, this behavior would be wrong.)

**Concern:**

Ticket says 'search persists across page reload (input + results in URL params or local state)' — but React component state is NOT persistent across reload. Only URL params or localStorage persist. Implementation must clarify whether search persistence on reload is required.

**Property:**

Transient UI state required to survive reload must be encoded in URL parameters or localStorage, not React component state alone.

**Implies:**
- Implies: Product decision: is search state persistence on reload required for v1?
- Implies: If yes: use URL params /search?q=rust&page=1&tags=tag1,tag2
- Implies: If no: update acceptance criteria to say search is cleared on reload
