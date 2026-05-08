## Scenario: User pauses a session mid-session, resumes later, completes

**Severity:** degradation

**Setup:**

David starts a 25-minute focus session at 10am. At 10:05am, he pauses it (5 minutes elapsed). At 10:30am, he resumes it. At 10:50am (30 minutes of real time later, but only 20 minutes more of focus time), the session completes.

The confusion flag in the story asks: "Does pausing mean the session doesn't count?" The contract doesn't clarify.

**Trigger:**

The session is logged to the event log upon completion.

**Expected:**

Two interpretations:

*Interpretation A:* Paused sessions count if completed.
- Daily review shows 1 completed focus session with duration = 25 minutes (the full timer duration).

*Interpretation B:* Paused sessions don't count.
- Daily review shows 0 completed focus sessions, or "pause doesn't count as completion."

**Concern:**

Without clarity on "what is a completed session," the event log and daily review are ambiguous. If the story says "completed sessions" but doesn't define what that means for paused sessions, the implementation will make an assumption. If David pauses and resumes repeatedly but never actually sits down for the full time, should those count? Should only "uninterrupted" sessions count?

This is a product/story clarity issue, but it manifests as a test-surface issue: the test must reflect the definition.

**Property:**

A clear definition must exist for session.status values:
- 'completed' must mean a specific thing (timeout with no pause? timeout even if paused? manual completion?)
- 'paused' might be a transient state that can become 'completed' later
- 'skipped' must be a terminal state (user pressed skip button)

**Implies:**

- Implies story clarification: what counts as "completed" for daily review? (flag for Alice)
- Implies contract note update: session status state machine must include pause/resume (flag for Tweedledee/Tweedledum)
- Implies test structure: dependent on above clarification
