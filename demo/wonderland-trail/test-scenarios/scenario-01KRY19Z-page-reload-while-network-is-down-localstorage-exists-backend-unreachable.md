## Scenario 277: Page reload while network is down: localStorage exists, backend unreachable

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GH
**Severity:** degradation

**Setup:**

User is editing a note with title 'Offline Research' and body 'Initial thoughts'. They hit F5 to reload. At that exact moment, their network goes down (WiFi drops). localStorage has the latest draft {title: 'Offline Research', body: 'Initial thoughts', ...}. Backend is unreachable (408 timeout, or ECONNREFUSED).

**Trigger:**

App boots. Editor or NoteList tries to fetch from backend. Network request times out or fails with 5xx/network error.

**Expected:**

Per the architecture (ADR-006), the app is hybrid-offline: keystroke buffer survives network loss, but the app should still boot gracefully. Editor should restore from localStorage and allow the user to continue editing (or save when network returns). NoteList should show a network error with a retry button, but not crash. The backend-fetch failure is recoverable.

**Concern:**

Currently, both Editor and NoteList independently handle fetch failures. Editor falls back to localStorage gracefully. But NoteList will show an error state, and if the user clicks Retry before network is restored, it will fail again. The current UX is correct for NoteList (show error, allow retry). But there's no coordinated app-level recovery: if the user navigates to Editor → NoteList → back to Editor during a network outage, each component re-fetches and might have inconsistent state. This is a degradation (not a breakage), because the app still works, but it might be confusing.

**Property:**

For all backend fetch failures (network timeout, 5xx, etc.): (1) Each component should fall back gracefully (Editor restores localStorage, NoteList shows error with retry), (2) The app should not require backend connectivity to boot into a usable state if localStorage has content, (3) Once network is restored, the app should re-sync without user intervention (or with a clear 'Sync' button).

**Implies:**
- Implies architectural decision: should the app cache the NoteList in localStorage and restore it on boot if backend is unreachable? Or should NoteList only show notes on a successful fetch? — flag for Cat.
- Implies missing contract: hybrid-offline semantics are not fully specified. When is backend required, when is it optional? What's the UX for 'network error, retry available'?
