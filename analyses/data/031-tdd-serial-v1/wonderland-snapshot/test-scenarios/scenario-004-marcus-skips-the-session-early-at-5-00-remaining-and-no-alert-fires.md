## Scenario 004: Marcus skips the session early (at 5:00 remaining), and no alert fires

**Severity:** degradation

**Setup:**

A focus session is running with 5:00 remaining. SKIP button is visible.

**Trigger:**

Marcus clicks SKIP.

**Expected:**

Session immediately ends. Display shows session complete. Start button enables for next session. No audio alert fires (skip is intentional exit, not timeout).

**Concern:**

Audio alert will fire on skip (should not). Session will not actually end. The skip will not be recorded in events.

**Property:**

skip_session() causes state -> completed AND completion_type == 'skip' (not 'timeout'). Audio alert does not fire.

**Implies:**
- Implies event logging: backend must distinguish skip from timeout completion (feature 003 will consume this).
