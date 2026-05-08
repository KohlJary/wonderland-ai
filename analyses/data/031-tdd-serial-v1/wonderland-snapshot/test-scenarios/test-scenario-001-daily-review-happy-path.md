## Scenario: David finishes his morning sessions and views daily stats

**Severity:** breakage

**Setup:**

David starts his workday at 8am PT. By 10am, he has:
- Completed 3 focus sessions (25 min, 25 min, 30 min)
- Completed 2 breaks between sessions
- Skipped 1 break (was in the middle of something)

All sessions occurred on the same calendar day (no midnight crossing).

**Trigger:**

David opens the daily review screen at 10:05am.

**Expected:**

The daily review shows:
- 3 completed focus sessions
- 2 completed breaks
- 1 skipped break
- 80 minutes total focus time

**Concern:**

The aggregation query must return the exact structure expected by the UI. If the query is missing columns, returns wrong type (string instead of int), or has off-by-one errors in the counts, the UI will either crash or display wrong numbers. The aggregation is simple (sum + count) but must be correct.

**Property:**

For all sets of sessions S completed on day D with types {focus_completed, break_completed, break_skipped}:
- count(focus_completed) must equal the number of sessions with type='focus' and status='completed'
- sum(duration_ms for focus_completed) must equal the total focus time
- count(break_completed) + count(break_skipped) must equal the total breaks initiated that day

**Implies:**

- Implies contract clarification: what exact fields does the daily-review query return? (artifact: contract-note-003)
- Implies backend API contract: GET /api/daily-review?date=YYYY-MM-DD must return structure with fields: completed_focus_count, completed_break_count, skipped_break_count, total_focus_time_ms
