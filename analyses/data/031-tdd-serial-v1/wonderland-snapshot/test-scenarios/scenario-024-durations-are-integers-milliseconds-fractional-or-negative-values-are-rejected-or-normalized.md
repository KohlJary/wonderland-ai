## Scenario 024: Durations are integers (milliseconds); fractional or negative values are rejected or normalized

**Severity:** degradation

**Setup:**

User on Settings or localStorage contains focus_duration_ms.

**Trigger:**

focus_duration_ms is set to 1500.5 (float), -5000 (negative), 0, or NaN.

**Expected:**

Values <= 0 are rejected or clamped to a minimum (e.g., 1*60*1000 = 1 minute minimum). Fractional values are accepted if they're valid milliseconds (e.g., 1500.5 is valid as 1.5 seconds), or rounded to integers if the system only supports integer ms. The persisted value is valid and will not cause the timer to behave unexpectedly.

**Concern:**

A negative duration could cause the timer to count backwards or malfunction. A zero or extremely small duration might cause the timer to immediately complete or enter a broken state. A float could cause rounding errors or type mismatches downstream.

**Property:**

For all values assigned to focus_duration_ms and break_duration_ms, the persisted value is a positive integer in milliseconds.
