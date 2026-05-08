## Scenario 008: User sets timer to 1 second duration (boundary condition)

**Severity:** curiosity

**Setup:**

Timer UI allows duration input. User enters '1' second.

**Trigger:**

User clicks START. Waits 1 second.

**Expected:**

Timer reaches completion and fires alerts correctly. No division-by-zero or off-by-one errors. MM:SS display shows 0:01 initially, then 0:00, then completion.

**Concern:**

MM:SS calculation may round or truncate incorrectly at very small durations. Alerts may not fire or fire multiple times. Display may flicker.

**Property:**

For all durations D in range [1000ms, 1500000ms], countdown is monotonically decreasing by exactly 1000ms per step, and completion fires exactly once.

**Implies:**
- Implies input validation: what's the minimum duration? Contract doesn't specify. If 1-second timers are out of scope, this scenario documents the boundary.
