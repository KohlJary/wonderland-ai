## Scenario 002: Marcus force-quits the app 10 seconds into his 25-minute session

**Severity:** degradation

**Setup:**

Marcus starts a session. The timer shows 24:50 remaining. No break is active. The app is in the middle of a countdown tick cycle.

**Trigger:**

The OS terminates the app (user swipes it away, system memory pressure, etc.).

**Expected:**

On restart, the app reads the in-flight session state from persistent storage. The timer resumes from approximately 24:50 (or slightly less, accounting for elapsed time). The session remains 'running'.

**Concern:**

In-memory session state will be lost. If the app only keeps the timer in RAM and does not periodically checkpoint to disk, restart loses the session progress. User has to start over.

**Property:**

For all sessions S in state 'running', the tuple (S.id, S.state, S.elapsed_time, S.session_type, S.started_at) is persisted to stable storage at least once per second.

**Implies:**
- Requires backend persistence contract — Tweedles must checkpoint session state, not just keep it in RAM.
