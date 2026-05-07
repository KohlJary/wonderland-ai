## Contract Note 002: Notification contract and failure semantics

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Not yet defined — stories reference 'user is notified' without specifying mechanism or guarantees

**Proposed Change:**

Notification delivery is a **frontend concern**. Backend does not deliver notifications. Client-side timers fire notifications (Web Notifications API, OS notifications, or fallback to page alert). Backend's responsibility is limited to: persisting that a session ended, timestamped. Failure semantic: if a notification doesn't fire (browser closed, browser doesn't support API, user denied permission), the session is still logged when it ends. The user can see the completed session in history even if they didn't hear about it in real time.

**Source:** Feature 001, Feature 002 (both reference 'notification when session/break ends'), ADR-001 (notification boundary question)

**Frontend Impact (Tweedledee):**

Frontend owns notification delivery. I run the session timer client-side, I fire Web Notifications API (with graceful fallback to page alert / tab title if API not available or permission denied). If the notification doesn't fire, the session *still completes and logs* — when the user checks the app later, they see the completed session in history. The notification is a *courtesy*, not the source of truth. Cost: straightforward — timer + notification API + fallback chain. No complex orchestration.

**Backend Impact (Tweedledum):**

Confirmed — you just persist the session record with timestamp. No notification delivery from backend.
