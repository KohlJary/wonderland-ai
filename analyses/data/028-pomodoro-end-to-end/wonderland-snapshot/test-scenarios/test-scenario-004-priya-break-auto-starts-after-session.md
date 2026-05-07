## Scenario: Priya completes a session; break timer automatically begins

**Severity:** breakage

**Setup:**
Priya has been in a 25-minute focus session. The timer shows 0:02 remaining. Her settings are default: 5-minute breaks.

**Trigger:**
The session timer expires (or Priya manually taps Stop).

**Expected:**
1. The session transitions to state=completed
2. Within 500ms, the UI transitions to a break screen
3. A 5-minute break timer appears and begins counting down
4. The break screen displays the message: "Take a break. Step away from your desk."
5. A "Skip Break" button is visible
6. A "Start Next Session" button is visible
7. /break/current returns {state: active, remaining_seconds: ~300}

**Concern:**
This is breakage because the break is core to the Pomodoro experience. Without
automatic break initiation, the feature is incomplete. If the break doesn't start
automatically, the user has to manually trigger it, which defeats the purpose of
pushing toward actual rest.

If break doesn't start:
- Users won't rest between sessions
- The product fails its core promise (structured focus with enforced rest)
- This is a flow-critical feature, not an edge case

**Property:**
For any completed session S with break_duration_minutes B from user settings:
- When session transitions to state=completed, create break record
- /break/current returns {state: active, remaining_seconds: <= B*60}
- Break is automatically in-flight; no explicit user action required to "start" break

**Implies:**
- Implies backend: on session→completed, automatically initialize break (not on-demand from client)
- Implies frontend: break state management must handle rapid session→break transition
