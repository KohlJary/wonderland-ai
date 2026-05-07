## Scenario 003: Marcus completes a session, the break auto-starts, but the app crashes before the break state is written — restart shows the session as still 'running'

**Severity:** silent-wrongness

**Setup:**

Marcus completes a 25-minute session. The state machine transitions to 'break'. The UI updates to show 'Break: 5:00'. The write to history is about to fire.

**Trigger:**

The app crashes or is killed before the SessionRecord write commits (e.g., OOM during the write, network timeout on a remote persist, disk full).

**Expected:**

On restart, the app detects the orphaned session, queries history to see if the session was already recorded. If yes, the session is closed and history is considered authoritative. If no, the session is presented as incomplete for the user to resolve.

**Concern:**

The app will restart and see the session still in 'running' state, unaware that it actually completed. The user sees the same session again and may try to resume it, double-counting the session in their history.

**Property:**

For all sessions S that transition from 'running' to 'break', the SessionRecord write is atomic with (or precedes) the state change. If the app restarts with an unfinished transition, it uses SessionRecord as the source of truth, not in-memory state.

**Implies:**
- Requires transaction design — Tweedles must decide whether state change or history write comes first, or if they're part of a single atomic operation.
