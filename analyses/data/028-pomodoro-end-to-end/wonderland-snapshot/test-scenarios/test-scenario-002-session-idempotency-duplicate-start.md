## Scenario: User's phone retries session start due to network flake; system returns existing session

**Severity:** silent-wrongness

**Setup:**
Marcus has tapped 'Start Session' once; the request reached the server and a session was created (state=active, session_id=42). But the response was lost in transit and never reached the client.

**Trigger:**
The client, seeing no response, retries POST /session/start after 3 seconds.

**Expected:**
POST /session/start returns 200 with session_id=42, the same session that was created on the first request. No new session (session_id=43) is created.

**Concern:**
If the system is not idempotent and the retry creates a second session, then:
- The user will have two active sessions in the database (constraint violation)
- The client will see conflicting data: /session/current might return session 42 or session 43 depending on timing
- The user's focus block history will be corrupted (two overlapping sessions)
- Silent wrongness: the app appears to work (timer runs, notification fires for one of them) but the data underneath is inconsistent

This violates the invariant "no two active sessions for a user at the same time."

**Property:**
For any user U:
- POST /session/start(U) returns a session S with state=active
- POST /session/start(U) issued again within the same logical operation (before session completes) returns the same session S with the same session_id
- At most one session with state=active exists for U at any moment

**Implies:**
- Implies backend: implement idempotency keying (either by session_id return or by rejecting if one is already active)
- Implies contract: clarify whether duplicate requests return 200 (idempotent) or 409 Conflict + existing session info
