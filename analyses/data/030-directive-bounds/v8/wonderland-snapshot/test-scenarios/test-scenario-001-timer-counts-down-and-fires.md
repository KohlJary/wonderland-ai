## Test Scenario: Timer counts down and fires notification when focus period expires

**Severity:** breakage

**Feature:** Feature 001: Run a focus session with breaks

**Setup:**

Backend has created a current_session in focus phase with 25 minutes duration, elapsed_time=0. Frontend polls GET /sessions/current every 1 second.

**Trigger:**

Elapsed time increments to 1500 seconds (25 minutes), triggering timer expiry logic.

**Expected:**

Backend transitions current_session from phase=focus to phase=break, records state=running. Frontend receives updated session state, dismisses focus timer, displays break timer starting at 5 minutes.

**Concern:**

Timer precision failure — if backend timer uses setInterval with imprecise clock advance (e.g., system load delays callback), elapsed_time skips or drifts. At 1500s boundary, precision loss causes timer to never fire (elapsed stays 1499s) or fires early (elapsed jumps to 1510s before transition). This is silent-wrongness territory: timer looks like it's running but doesn't fire.

**Property:**

For all focus sessions S with duration D, there exists a time T where elapsed_time >= D AND backend has transitioned phase from focus to break (monotonic, one-way).

**Implications:**

- Backend timer implementation detail — Tweedledum owns the setInterval vs. scheduled job question.
- Frontend polling accuracy — does 1-second granularity suffice for user perception or does sub-second matter?
