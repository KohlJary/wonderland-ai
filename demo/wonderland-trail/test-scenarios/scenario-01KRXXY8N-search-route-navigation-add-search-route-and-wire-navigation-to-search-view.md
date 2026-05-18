## Scenario Set: Search Route Navigation (Ticket 037 - Add search route and wire navigation to search view)

**Ticket:** ticket-01KRXX3S-add-search-route-and-wire-navigation-to-search-view
**Feature:** kohl-searches-notes-by-title-and-body-content
**Iteration:** add-search-route-and-wire-navigation-to-search-view

---

### Scenario 1: Search route is navigable and renders component

**Severity:** breakage

**Setup:**
- App.tsx is being refactored from view-state toggle (`useState('editor' | 'search' | 'list')`) to React Router
- Routes `/notes` and `/search` are registered with their respective components
- Navigation buttons use `useNavigate` instead of `setState`
- NoteList has a Search button that calls `useNavigate('/search')`

**Trigger:**
User clicks the "🔍 Search" navigation button while viewing the notes list.

**Expected:**
- Browser URL changes to `/search` (visible in address bar)
- Search component mounts and renders with empty input field ready for typing
- No console errors, no blank page, no 404

**Concern:**
React Router may not be installed or integrated into the app. The `/search` route may not be registered in the router configuration. The navigation button may still use `setState` instead of `useNavigate`. Component import may fail. Without a proper router, the route will not exist.

**Property:**
For all routes R registered in the React Router configuration with an assigned component, navigating to R must update the browser URL to match R and render the correct component without error.

**Implies:**
- Implies: React Router is installed (`react-router-dom` package) and `<BrowserRouter>` wraps the route definitions in main.tsx or App.tsx
- Implies: `/search` route is registered via `<Route path='/search' element={<Search />} />`
- Implies: Navigation buttons use `useNavigate` hook or `<Link>` component, never `setState`
- Implies: App initialization does not depend on navigating through UI; direct navigation to `/search` must work

---

### Scenario 2: Browser back button returns from search to notes with intact history

**Severity:** breakage

**Setup:**
- User has navigated from `/notes` to `/search` (browser history stack contains both routes)
- User is currently viewing `/search`
- Browser back button is clickable

**Trigger:**
User presses the browser back button (or clicks native browser back button).

**Expected:**
- Browser URL changes back to `/notes`
- NoteList component renders
- Browser history is intact (stepping back through route changes works correctly)
- No blank page or error

**Concern:**
If the implementation still uses `setState` for view switching (the old pattern in App.tsx), the back button will not step through React state changes, because `setState` does not create browser history entries. React Router handles browser history automatically, but only if all navigation uses `useNavigate` or `Link`, not `setState`.

**Property:**
All route transitions must create entries in browser history. The back button must step through route history in reverse chronological order without gaps or jumps.

**Implies:**
- Implies: Use React Router's `<BrowserRouter>` (not `MemoryRouter` or `HashRouter`), which integrates with the browser's history API
- Implies: All navigation must use `useNavigate(path)` or `<Link to={path} />`, never `setState` for view changes
- Implies: No hybrid navigation (some routes via router, some via setState) — all must use router

---

### Scenario 3: Search state (query, pagination) is lost on page reload if not encoded in URL

**Severity:** degradation

**Setup:**
- User has typed "rust" in the search input
- Backend returned search results
- User is viewing page 2 of results with a tag filter applied
- URL is `/search` (no query parameters encoding the search state)
- Only React component state holds the query and pagination values

**Trigger:**
User presses F5 (or Cmd+R on macOS) to reload the page.

**Expected Behavior (if URL params are NOT used):**
- Page reloads to `/search`
- Search component initializes with empty input field and no results
- This is expected behavior if search state is not persisted in URL

**Concern:**
The ticket's acceptance criteria say "Search persists across page reload (input + results in URL params or local state)" — but this is ambiguous. "Local state" in React typically means component state, which is NOT persistent across a page reload; only URL parameters or localStorage are persistent. If the implementation relies only on component state and does not encode search terms in URL params, the search will be lost on reload, violating this acceptance criterion.

**Property:**
For any UI state that must survive a page reload, that state must be encoded in the URL (as query parameters: `?q=rust&page=2&tags=tag1,tag2`) or persisted to browser localStorage or a backend service. React component state alone cannot survive a reload because the component unmounts and remounts with initial state.

**Implies:**
- Implies: Product clarification is needed: must search state persist across page reload for v1?
- Implies: If YES (state must persist): use URL query parameters like `/search?q=rust&page=2&tags=tag1,tag2` to encode all search state
- Implies: If NO (state may be cleared): update the acceptance criteria to state explicitly that "search is cleared on page reload" to avoid ambiguity
- Implies: If localStorage is used for persistence, that choice should be documented in the implementation

---

### Scenario 4: Search state is encoded in URL params; back button and reload both preserve search

**Severity:** degradation

**Setup:**
- Implementation uses URL query parameters to encode search state: `/search?q=rust&page=2&tags=tag1`
- Component state is kept in sync with URL params using React Router's `useSearchParams` hook
- User has typed a query, paginated, and selected tag filters

**Trigger:**
- Case A: User presses F5 to reload the page
- Case B: User navigates away and back via browser back/forward buttons
- Case C: User directly navigates to a URL with query params like `/search?q=rust&page=2`

**Expected:**
- Case A (reload): Page reloads to `/search?q=rust&page=2&tags=tag1`. Search component reads params from URL and restores state. Results are shown again.
- Case B (back/forward): Browser history navigation preserves the full URL including params. Back button shows previous search state, forward button shows next search state.
- Case C (direct navigation): Typing `/search?q=rust&page=2` into address bar results in search being executed with those params.

**Concern:**
Syncing component state with URL params is error-prone. If state and URL params diverge (e.g., user types a query but the URL doesn't update), back button navigation becomes unpredictable. React Router's `useSearchParams` hook handles this, but it must be used correctly. Component state updates must call the setter from `useSearchParams`, not a separate `useState`.

**Property:**
If search state is persisted in URL parameters, all changes to search state must immediately update the URL params, and all URL param changes must immediately update component state. The two must remain synchronized.

**Implies:**
- Implies: Use React Router's `useSearchParams()` hook to read and write query parameters, not manual URL manipulation
- Implies: Do not use both `useSearchParams` and a separate `useState` for search state — choose one
- Implies: Component state should be derived from URL params, not the other way around (URL is the source of truth)

---

### Scenario 5: User navigates directly to /search via URL bar; page loads correctly

**Severity:** breakage

**Setup:**
- React Router is configured with `/search` route
- User has not navigated through the app's UI; they are accessing the app for the first time
- User types `/search` directly into the browser's address bar, or a bookmarked link goes directly to `/search`

**Trigger:**
Browser navigates directly to `/search` (not via clicking a button in the app).

**Expected:**
- App loads (React and router initialize)
- Router recognizes `/search` and renders the Search component
- Search component mounts with empty input (initial state) or restored state (if URL params are used)
- No 404, blank page, or error

**Concern:**
Some SPAs don't support deep linking: they require navigating through the app's UI in a specific order to initialize properly. If the app has initialization code that assumes a specific route order (e.g., assumes `/notes` is always loaded first), direct navigation to `/search` may fail.

**Property:**
All registered routes must be directly navigable via URL without requiring prior navigation through the app's UI.

**Implies:**
- Implies: React Router configuration is complete; all supported routes are registered
- Implies: App initialization does not depend on route navigation order or which route is accessed first
- Implies: No hardcoded assumptions about route sequencing

---

### Scenario 6: User leaves /editor view with unsaved draft, navigates to /search, back button returns to /editor — draft is gone

**Severity:** degradation

**Setup:**
- User is on `/editor` (EditorLayout component)
- User has typed a note title and body but has not clicked "Save"
- Editor state is stored in React component state (or possibly localStorage, if that's used)
- User clicks the "🔍 Search" navigation button

**Trigger:**
- User clicks "Search" button and navigates to `/search`
- Editor component unmounts (view changes via router)
- User then clicks browser back button to return to `/editor`

**Expected:**
- URL changes back to `/editor`
- EditorLayout component mounts again
- State is either: (A) empty (draft was lost), or (B) restored from localStorage (draft survived)
- Ticket does not specify which behavior is desired

**Concern:**
If drafts are stored only in React component state, they will be lost when the component unmounts and remounts. If localStorage is used, drafts will persist. The ticket does not address draft preservation, so the implementation must make a choice. This is a UX risk: users may lose work if they navigate away without saving.

**Property:**
If a component's state should survive unmounting and remounting, that state must be persisted to localStorage or a backend service, not kept only in React memory.

**Implies:**
- Implies: Product decision: should unsaved editor drafts survive navigation away from `/editor`?
- Implies: If YES: use localStorage to persist draft state
- Implies: If NO: acceptable to lose draft on navigation (but may want a confirmation dialog: "You have unsaved changes")
- Implies: UX consideration: should there be a confirmation dialog or warning when leaving `/editor` with unsaved content?

---

### Scenario 7: Search route path is consistent (/search, not mixed with /notes/search or typos)

**Severity:** degradation

**Setup:**
- Ticket says "Add search route (e.g., /notes/search or /search)" but does not mandate a specific path
- Implementation chooses a path: either `/search` or `/notes/search`
- Navigation buttons, tests, and route registration must all reference the same path

**Trigger:**
Implementation registers the route and creates navigation links.

**Expected:**
- All references to the search route use the same path consistently:
  - `useNavigate('/search')` in navbar
  - `<Route path='/search' element={<Search />} />` in router config
  - Tests assert navigation to `/search`
  - Documentation and contracts specify `/search`
- No typos like `/serach` or mixed paths like `/search` in some places and `/notes/search` in others

**Concern:**
If different parts of the codebase use different route paths (e.g., navbar uses `/search`, but one router registration uses `/notes/search`), navigation will be broken or inconsistent. This is a coordination issue across the frontend implementation.

**Property:**
All code references to the search route must use the same URL path.

**Implies:**
- Implies: Route path should be chosen once and documented (e.g., in a contract note, README, or Tweedle pair discussion)
- Implies: Code review should check for consistency of path references across navbar, router config, and tests
- Implies: If route path changes, all references must be updated together

---

### Scenario 8: Multi-view navigation chain: /notes → /search → /editor; back button steps through correctly

**Severity:** degradation

**Setup:**
- User navigates from `/notes` to `/search` (first navigation)
- User then navigates from `/search` to `/editor` (second navigation)
- Browser history stack is now `[/notes, /search, /editor]`
- User is currently at `/editor`

**Trigger:**
- User presses browser back button (first time)
- User presses browser back button again (second time)

**Expected:**
- First back press: URL changes to `/search`, Search component renders
- Second back press: URL changes to `/notes`, NoteList component renders
- History is stepped through in correct LIFO (last-in-first-out) order
- No skipping, no jumping to wrong view

**Concern:**
If React Router's history management is incomplete or if there are custom history manipulations, the back button may skip entries, jump to the wrong route, or show unpredictable behavior. This tests correctness of multi-step navigation chains.

**Property:**
Browser history must be a LIFO stack. Each back button press must pop one route from the stack and navigate to the previous route, in reverse chronological order.

**Implies:**
- Implies: React Router integration with browser history API (`window.history`) is working correctly
- Implies: No custom history manipulation that could corrupt the LIFO order

---

## Summary: Grin Equivalents

Each scenario above names a specific failure mode that the implementation must handle:

1. **Breakage**: Router not set up, route not registered, navigation broken
2. **Breakage**: Back button doesn't work (history not managed by router)
3. **Degradation** (or acceptance ambiguity): Search state lost on reload (acceptable if URL params not used)
4. **Degradation**: State/URL param sync problems if URL-based persistence is used
5. **Breakage**: Direct route navigation fails
6. **Degradation**: Draft loss on navigation (UX issue, acceptable if confirmed)
7. **Degradation**: Route path inconsistency across codebase
8. **Degradation**: Multi-step navigation history incorrect

The **grin equivalent** for this scenario set is: **all references to the search route are consistent, all navigation uses React Router (not setState), and back button correctly steps through browser history**. If the implementation uses router-based navigation throughout, these scenarios will pass.
