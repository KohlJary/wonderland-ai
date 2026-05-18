## Scenario 189: User navigates /notes → /search → /editor, presses back button twice, steps through /search to /notes correctly

**GUID:** 01KRXYDBED29B1DN9NNN3336YN
**Severity:** degradation

**Setup:**

Browser history stack is [/notes, /search, /editor]. User is at /editor.

**Trigger:**

User presses back button once, then again.

**Expected:**

First back: URL changes to /search. Second back: URL changes to /notes. History steps through LIFO order without skipping.

**Concern:**

If React Router history management is incomplete, back button may skip entries or jump to wrong route. Tests multi-step navigation correctness.

**Property:**

Browser history must be LIFO. Back button must pop one route at a time in reverse chronological order.

**Implies:**
- Implies: React Router integration with browser history API is correct
- Implies: No custom history manipulation that corrupts LIFO order
