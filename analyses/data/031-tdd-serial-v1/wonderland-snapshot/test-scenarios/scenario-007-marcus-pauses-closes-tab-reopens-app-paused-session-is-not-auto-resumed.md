## Scenario 007: Marcus pauses, closes tab, reopens app: paused session is NOT auto-resumed

**Severity:** curiosity

**Setup:**

A focus session is running, then paused. User closes the browser tab completely. User reopens the app in a fresh tab.

**Trigger:**

The app loads fresh (fresh JS runtime).

**Expected:**

The previous session is NOT automatically resumed. A new session must be explicitly started.

**Concern:**

This is a clarification point from the story confusion-flag. The contract doesn't specify session persistence across page reloads. If persistence is intended, we need recovery logic. This scenario documents: no persistence assumed for Feature 001.

**Property:**

Session state lives in frontend JavaScript, not persistent storage. Page reload = fresh state, ready for new start.

**Implies:**
- Implies clarification for next iteration: Feature 004 (persistent settings) may add session state recovery. Flag for Caterpillar and Rabbit.
