## Scenario 284: GET /notes is called on app boot; 150 notes are returned; frontend must not freeze during rendering

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQBZ
**Severity:** degradation

**Setup:**

Backend has 150 notes (realistic for a researcher who works regularly). All have 2-5 tags each. GET /api/notes returns the full array in reverse chronological order (150 items × ~500 bytes per item ≈ 75KB payload).

**Trigger:**

Kohl opens the app. App.useEffect calls listNotes(), which calls GET /api/notes and receives all 150 notes.

**Expected:**

GET /api/notes completes in <100ms (fast query, no N+1, efficient serialization). Frontend NoteList component receives the array. React renders the list with virtualization or pagination so the initial paint (<3s target) happens even if 150 items are in the result. Kohl sees the list and can scroll to browse notes. No browser freeze, no white screen for >3s.

**Concern:**

If the backend query N+1s on tags (one SELECT per note to fetch tags), response time degrades to 1-5s for 150 notes. If the frontend renders all 150 items without virtualization, React reconciliation could stall the main thread and cause jank. Either backend or frontend slowness breaks Kohl's perceived responsiveness.

**Property:**

get_notes_scales_to_100_notes_sub_3s_perceived_time
