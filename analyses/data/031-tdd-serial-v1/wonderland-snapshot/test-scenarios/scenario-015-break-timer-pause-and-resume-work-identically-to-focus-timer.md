## Scenario 015: Break timer pause and resume work identically to focus timer

**Severity:** degradation

**Setup:**

Break timer is running, elapsed_ms=30000 (30 seconds into a 5-minute break).

**Trigger:**

User taps pause. Then, 10 seconds wall-clock later, taps resume.

**Expected:**

Pause returns status='paused' with elapsed_ms=30000. While paused, elapsed_ms remains 30000. Resume returns status='running' with elapsed_ms=30000 (same as pause moment, not advanced).

**Concern:**

If implementation handles 'type' field differently between focus and break, pause might not work on break. If system continues counting elapsed_ms during pause (wall-clock-based), resume will show wrong elapsed time.

**Property:**

Pause freezes elapsed_ms. Resume continues from the frozen value, not from current wall time.
