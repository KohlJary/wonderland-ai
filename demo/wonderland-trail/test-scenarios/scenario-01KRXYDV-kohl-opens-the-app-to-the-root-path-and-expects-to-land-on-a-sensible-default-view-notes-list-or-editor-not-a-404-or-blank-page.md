## Scenario 200: Kohl opens the app to the root path (/), and expects to land on a sensible default view (notes list or editor, not a 404 or blank page)

**GUID:** 01KRXYDVNXZN8XM83A00MPY61C
**Severity:** breakage

**Setup:**

Kohl closes the app and returns to it by typing the domain into the address bar. The browser navigates to the root path '/'

**Trigger:**

The app loads. React Router evaluates the route '/' against the defined routes (/editor, /search, /notes, etc.)

**Expected:**

The app displays a sensible default: either the notes list (if it exists), the editor pane (if that's the primary view), or a homepage/landing view. No 404 error, no blank page. The navigation menu is visible and functional

**Concern:**

If the router does not have a default route handler for '/', the app displays a 404 or blank screen. This is a breakage: the feature is unusable from the root path. Users who bookmark the domain or return via browser history will land in a broken state

**Property:**

root path routes to a valid view without errors
