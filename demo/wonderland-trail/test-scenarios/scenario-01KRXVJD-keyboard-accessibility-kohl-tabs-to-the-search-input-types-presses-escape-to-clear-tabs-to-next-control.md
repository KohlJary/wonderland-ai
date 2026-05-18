## Scenario 103: Keyboard accessibility: Kohl tabs to the search input, types, presses Escape to clear, tabs to next control

**GUID:** 01KRXVJD1AD0E3PGKD4RWZHY49
**Severity:** degradation

**Setup:**

App has editor and search UI.

**Trigger:**

Kohl uses keyboard navigation (Tab, Shift+Tab, Escape) to interact with search.

**Expected:**

Focus management works. Search input is accessible. Escape clears the search.

**Concern:**

If the search input isn't labeled properly, screen readers won't identify it. If there's no Escape handler, Kohl has to manually delete the text. If Tab order is odd, keyboard navigation is broken.

**Property:**

Search UI is keyboard-accessible and follows standard patterns (ARIA labels, logical tab order, Escape to clear).

**Implies:**
- Implies accessibility review — flag for Queen.
