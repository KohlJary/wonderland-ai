## Test Scenario 004: Session logging is independent of notification delivery

**Feature:** Feature 001 (Start, run, complete focus session)
**Severity:** degradation

### Setup

A session was running client-side for 25 minutes. The timer fired and the session ended. However, the Web Notifications API was blocked by the browser, so no notification appeared to the user.

### Trigger

Client completes the session and sends end request to backend, even though no notification was shown.

### Expected

Backend accepts and records the session. History will show the completed session the next time the user opens the app, even if they never saw a notification. Session data is not lost due to notification failure.

### Concern

If notification delivery were a prerequisite for session logging, a user could lose session data because their notification permission was revoked by the browser or system. The contract decouples these: notifications are UX only; sessions are logged regardless.

This is critical for mobile devices where notification permissions change frequently.

### Property

For all sessions S, existence(S in history) is independent of existence(notification_shown(S)). Notification failure does not prevent session persistence.

### Implies

- **Backend-Frontend contract**: Backend persists sessions on POST /sessions regardless of notification status. Frontend is responsible for notification UX only.
