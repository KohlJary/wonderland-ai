## Test Scenario: Session durations at min/max boundaries

**Severity:** degradation

**Feature:** Feature-003 & Feature-001 (settings + session execution)

**Setup:**

Riley (customization persona) sets focus duration to the minimum allowed (5 minutes) and break duration to the maximum allowed (30 minutes). Starts a session with these settings.

**Trigger:**

1. PATCH /settings with focus_duration_seconds=300 (5 min), break_duration_seconds=1800 (30 min)
2. POST /sessions/start with these custom durations
3. Frontend's timer counts down from 5:00
4. Session completes after 300 seconds (wall-clock elapsed)
5. POST /sessions/complete

**Expected:**

Session completes successfully with exact durations recorded:
- focus_duration_seconds = 300
- Session history shows 5 minutes logged

Break is then 30 minutes (the max allowed). After break completes:
- break_duration_seconds = 1800
- Session history shows 30 minutes logged for the break

Both settings applied correctly. No off-by-one errors on duration calculations.

**Concern:**

Boundary value bugs are common. Possible failures:
1. Off-by-one error: 5-minute session recorded as 4:59 (timer fires 1 second early)
2. Truncation: 5 minutes internally stored as 5.0 but displayed as 4:59 due to rounding
3. Database type mismatch: duration stored as FLOAT but compared with INT, causing type coercion bugs
4. Settings validation rejecting 5 min as "less than minimum" due to a >= vs > boundary check error

**Property:**

For all valid (focus_duration_seconds, break_duration_seconds) pairs within the allowed ranges:
- 5 min <= focus_duration_seconds <= 60 min (in 1-second precision)
- 1 min <= break_duration_seconds <= 30 min (in 1-second precision)

When a session completes with elapsed_seconds equal to the posted duration, the recorded session must have those exact values. No truncation, rounding, or off-by-one errors.

**Mechanism:**

Backend validation must use:
- focus_duration_seconds >= 300 AND focus_duration_seconds <= 3600 (not > 300, not < 3600)
- break_duration_seconds >= 60 AND break_duration_seconds <= 1800

Storage must use integer seconds (not float). Timer comparison must be exact (elapsed == duration, not >= or <).

**Implies:**

- Testing should also cover non-boundary values (e.g., 25:30, 15:17) to ensure precision isn't just lucky at boundaries
- May imply frontend timer precision issue: if frontend's setInterval doesn't tick exactly every 1000ms, elapsed_seconds can drift

**Runnable Tests:**

- `tests/test_settings_and_sessions_edge_durations.py::test_minimum_focus_duration_5_minutes_works`
- `tests/test_settings_and_sessions_edge_durations.py::test_maximum_break_duration_30_minutes_works`
- `tests/test_settings_and_sessions_edge_durations.py::test_non_round_duration_values_precision`
