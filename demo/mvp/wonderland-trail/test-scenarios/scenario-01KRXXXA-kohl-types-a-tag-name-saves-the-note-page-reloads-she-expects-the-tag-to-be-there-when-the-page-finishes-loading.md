## Scenario 151: Kohl types a tag name, saves the note, page reloads; she expects the tag to be there when the page finishes loading

**GUID:** 01KRXXXAWK63FBTGKJSS5NBRY3
**Severity:** degradation

**Setup:**

Kohl has typed a note title 'Performance observations' and body text. She types 'performance-tuning' into the tag input, presses Enter (tag appears as a chip), and immediately clicks Save. The browser begins the POST request to /api/notes.

**Trigger:**

While the POST request is in flight (0–2 seconds), the page accidentally reloads (user hits refresh, network hiccup causes browser to retry, etc.).

**Expected:**

After the page reloads and the editor re-hydrates, the 'performance-tuning' tag is visible in the tag input area. The note's title, body, and tags are all present and correct. No error message appears.

**Concern:**

If the tag is lost during the reload (localStorage was cleared but the backend save hasn't completed yet, or the hydration logic doesn't check the localStorage buffer for unsaved tags), Kohl loses her organizational metadata. She will have to re-add the tag and re-save.

**Property:**

Keystroke buffer recovery includes tags: localStorage buffer stores title, body, AND tags; on page reload, the buffer is restored before attempting to fetch from the backend.

**Implies:**
- The localStorage buffer must include tag_names alongside title and body.
- On mount, the component must restore from localStorage if present (even if the backend hydration is slower).
- If a simultaneous network request to save is in flight, the browser reload should NOT clear localStorage until the response confirms the save succeeded.
