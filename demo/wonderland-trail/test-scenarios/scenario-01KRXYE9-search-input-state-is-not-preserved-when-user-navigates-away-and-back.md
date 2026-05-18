## Scenario 205: Search input state is not preserved when user navigates away and back

**GUID:** 01KRXYE929PR8CE0PNGR2QFKHK
**Severity:** degradation

**Setup:**

Kohl types 'transformer' in the search input and sees 5 matching results. She clicks on one result to open the note. She then uses a back button (or navigation) to return to the search view.

**Trigger:**

Kohl navigates back to the search view.

**Expected:**

The search input still shows 'transformer' and the results list is still displayed (per ticket acceptance: 'Preserve search input across navigation so user can refine without retyping').

**Concern:**

If the search view component is unmounted when Kohl navigates away, and the state is not persisted (via URL query params or localStorage), the input is cleared and results are gone when she returns. She must re-type her query.

**Property:**

For all search terms Q that produce results, navigating away and returning to the search view preserves Q and the result list until Kohl explicitly clears the input.

**Implies:**
- Implies frontend state concern: Store search query in URL (e.g., /search?q=transformer) or localStorage. This also enables browser back/forward and sharing results via URL.
