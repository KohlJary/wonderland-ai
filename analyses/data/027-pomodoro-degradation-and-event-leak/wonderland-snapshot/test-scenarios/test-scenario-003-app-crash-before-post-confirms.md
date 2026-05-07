## Scenario: User starts a session; before POST /sessions confirms, user closes the app

**Severity:** silent-wrongness

**Setup:**
App is open. User taps 'Start Session' with targetDuration=25 minutes. The frontend initiates POST /sessions. The network request is in flight (HTTP layer, not yet completed). The response has not arrived at the client.

**Trigger:**
Before the server responds (or before the response is processed), user force-closes the app (kill process, pull tab, restart device, etc.).

**Expected (stable outcome):**
One of two outcomes: 
- (A) The session was created on the server, the app re-reads it on startup via GET /sessions?fromDate=today, resumes the timer from elapsed time (server's startTime + elapsed = now), and the user can continue.
- (B) The session was never created (POST was lost in-flight or rejected), the app shows no session on startup, and the user can start a new session without duplication.

**NOT expected (failure mode):**
A new POST is issued on restart (due to retry-retry-retry logic), creating two sessions: one on the server (from the original POST, which did succeed), and another (from the restart). The user sees duplicate sessions or the timer starts over from scratch.

**Concern:**
This scenario reveals that idempotent creation is a load-bearing contract. If the frontend uses server-assigned IDs (auto-increment), a retry will create a new session. If the POST request *did* succeed (server received it) but the response was lost (network failure on the way back), the client never learns the session was created. On restart, the client's local state shows no session, and a new POST is issued, creating a duplicate. The silent wrongness is that two sessions are created with nearly identical startTimes, and the user or backend might merge them, creating a ghost session.

Recovery requires either:
- Client-chosen ID (UUID): POST /sessions{...} where the client chooses ID. The server stores by ID and ignores duplicate POSTs with the same ID.
- Or: app restart queries GET /sessions?fromDate=today to recover any sessions created server-side but lost client-side.

Or both.

**Property:**
For all sessions: either the session is created exactly once on the server (idempotent creation via request deduplication or ID chosen by client), or the app has a recovery procedure on restart that either resumes a lost session or acknowledges the loss and does not double-create.

**Implies:**
- Implies idempotent API design: POST /sessions should be safe to retry. Either use client-provided UUID (idempotent key) or implement request deduplication on the backend. Flag for Tweedledum.
- Implies startup recovery: app must query GET /sessions?fromDate=today on restart to catch any sessions started but not locally confirmed. Merge recovered sessions with local state. Flag for Tweedledee.
- Implies contract: session record must include a unique client-generated ID (UUID) or the API must support idempotency keys. Flag for contract review.
