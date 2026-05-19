## Scenario 184: User at /search presses browser back button, navigates to /notes with correct browser history

**GUID:** 01KRXYDBED29B1DN9NNN3336YG
**Severity:** breakage

**Setup:**

User navigated from /notes to /search. Browser history stack contains both routes. Back button is clicked.

**Trigger:**

User presses browser back button while viewing /search.

**Expected:**

Browser URL changes to /notes. NoteList component renders. Browser history is correct (back button works).

**Concern:**

If setState-based view switching is still used, back button won't work because setState doesn't create history entries. React Router handles history automatically, but only if all navigation uses useNavigate or Link, not setState.

**Property:**

All route transitions must update browser history. Back button must step through route history in reverse order.

**Implies:**
- Implies: Use React Router's <BrowserRouter>, which integrates with browser history API
- Implies: All navigation must use useNavigate or <Link>, never setState for view changes
- Implies: No hybrid navigation patterns
