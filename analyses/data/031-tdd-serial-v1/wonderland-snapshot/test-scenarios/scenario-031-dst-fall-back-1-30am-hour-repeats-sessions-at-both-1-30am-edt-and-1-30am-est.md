## Scenario 031: DST fall-back: 1:30am hour repeats; sessions at both 1:30am EDT and 1:30am EST

**Severity:** curiosity

**Setup:**

Nov 5 2023 (hypothetically): 2:00am EDT→1:00am EST. Hour 1:00-2am repeats. Derek completes sessions at 1:30am (first) and 1:30am (second, 1 hour later UTC).

**Trigger:**

Streak query includes both in calculation.

**Expected:**

Both recorded (different UTC times). Streak counts both (two sessions on transition day, despite same wall-clock time).

**Concern:**

If timestamps not UTC-internal, repeated hour is ambiguous. Correct impl uses UTC, no ambiguity.

**Property:**

All timestamps internally UTC. Wall-clock ambiguity (repeated hour) resolved at storage.
