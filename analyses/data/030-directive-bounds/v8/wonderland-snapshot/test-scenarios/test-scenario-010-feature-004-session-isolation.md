## Test Scenario 010: Session isolation by session_id (Feature 004)

**Feature:** Use the app without sign-up
**Severity:** critical

**Scenario:**

Two clients A and B make requests with different session_ids (UUID1 and UUID2). Client A starts a session, completes it, and writes it to the database. Client B requests GET /api/sessions. Client B should see zero sessions (their own history is empty), not Client A's session. The sessions table is partitioned by session_id; reads/writes for UUID1 are isolated from UUID2.

**What breaks if this fails:**

Users see each other's data. Privacy is completely broken. A user's streak is contaminated by strangers' sessions.

**Acceptance Criteria:**

- Client A starts session with session_id=UUID1, completes it
- Client B requests GET /api/sessions with session_id=UUID2
- Client B receives 200 with empty list []
- Database sessions table has exactly one row (Client A's), not two
- Client A requesting GET /api/sessions with session_id=UUID1 returns their one session
- Settings updates by Client A (session_id=UUID1) do not affect Client B's settings (session_id=UUID2)
