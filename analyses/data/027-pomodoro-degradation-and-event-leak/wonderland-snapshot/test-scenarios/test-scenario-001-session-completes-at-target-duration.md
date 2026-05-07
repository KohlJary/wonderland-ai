## Scenario: Session completes exactly at target duration; user receives notification

**Severity:** breakage

**Setup:**
A focus session created with targetDuration=25 minutes. User starts the timer. Real time is the moment of session creation (t=0).

**Trigger:**
Real time advances exactly 25 minutes. The system's clock reaches the session's startTime + 25 minutes.

**Expected:**
Session state transitions to 'completed'. A notification is delivered (visual, audio, or both). The session record is persisted with actualDuration=25 and completionStatus='completed'.

**Concern:**
I suspect the team hasn't pinned what 'notification' means in the contract — is it browser Notification API? Or something else in the frontend? I also suspect the timer implementation will count down client-side but the completion event will race the user's interaction — the user might tap 'extend' at second 24, then the timer fires at second 25. What wins? I also suspect the session might get created (POST to /sessions) but never persisted if the POST request to the server hasn't confirmed yet. If the user closes the app before POST confirms, the session exists on the server but the client doesn't know about it, and a restart might create a duplicate.

**Property:**
For all sessions with actualDuration >= targetDuration, the session must transition to completionStatus='completed' exactly once, and a notification must fire exactly once. No silent loss of completion events. No duplicate completion notifications.

**Implies:**
- Implies timing assumption: real wall-clock time, not logical-clock or event-driven time. Flag for Cat.
- Implies notification surface: what API? browser Notification? What happens if notification permission is denied? Flag for Cat or Tweedledee.
- Implies persistence guarantee: POST /sessions must be durable before timer is armed. If app crashes before POST confirms, startup recovery must re-query to catch the server-created session. Flag for Tweedledee.
