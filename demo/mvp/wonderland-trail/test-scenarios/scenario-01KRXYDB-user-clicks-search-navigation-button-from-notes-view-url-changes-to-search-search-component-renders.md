## Scenario 183: User clicks Search navigation button from notes view, URL changes to /search, search component renders

**GUID:** 01KRXYDBED29B1DN9NNN3336YF
**Severity:** breakage

**Setup:**

App.tsx is refactored from view-state toggle to React Router. Routes /notes and /search are registered with components. Navigation buttons use useNavigate. NoteList has a Search button that calls useNavigate('/search').

**Trigger:**

User clicks the '🔍 Search' button while viewing notes.

**Expected:**

Browser URL changes to /search. Search component renders with empty input field. No 404, no blank page, no console errors.

**Concern:**

React Router may not be installed or configured. /search route may not be registered. Navigation button may still use setState instead of useNavigate. Component import may fail. Without proper router setup, the route will not exist.

**Property:**

For all routes R in the router configuration with an assigned component, navigating to R must update the browser URL and render the correct component without error.

**Implies:**
- Implies: React Router is installed and <BrowserRouter> wraps route definitions
- Implies: /search route is registered with Search component via <Route path='/search' element={<Search />} />
- Implies: Navigation buttons use useNavigate hook or <Link>, not setState
- Implies: App initialization does not depend on route navigation order; direct /search access must work
