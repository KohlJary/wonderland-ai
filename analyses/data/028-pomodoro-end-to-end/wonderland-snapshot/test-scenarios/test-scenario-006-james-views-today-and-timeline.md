## Scenario: James opens the History tab and sees today's session count and timeline

**Severity:** breakage

**Setup:**
James completed 4 sessions today:
- 10:15 AM — 25 min
- 11:00 AM — 25 min  
- 2:00 PM — 25 min
- 2:30 PM — 25 min (just now)

**Trigger:**
James taps the History tab to check his progress before deciding if he has time for another block.

**Expected:**
1. History tab shows "4 sessions today"
2. Below: a timeline with each session listed by start time and duration
   - Each entry shows start time and duration: "10:15 AM — 25 min"
3. Total focus time displayed: "100 minutes today" or equivalent
4. All four sessions appear, ordered by completion time (most recent first)
5. The display updates in real-time if James completes another session while viewing

**Concern:**
This is breakage because the core use case is "know how many sessions I've done so I
can plan my day." Without accurate session history:
- James can't remember if he's completed 2 or 4 sessions
- He can't decide if he has time for another block
- He loses the ability to self-monitor progress
- The product fails a core acceptance criterion

If history is missing, wrong, or slow-to-update, the feature is broken.

**Property:**
For any user U with N completed sessions today:
- GET /sessions/history returns array of N sessions
- Each session has start_time (ISO 8601), completed_at (ISO 8601), duration_seconds
- Sessions are ordered by completed_at DESC (most recent first)
- Total duration = sum of all duration_seconds
- Queries filtered by today's date boundary are accurate to within 1 second

**Implies:**
- Implies backend: index on (user_id, completed_at) for fast queries
- Implies frontend: real-time update on session→completed event, not polling
