## Contract Note 007: POST /auth/login response shape

**State:** agreed
**Contract Version:** v1

**Current Shape:**

Contract-002 v1 says 'POST /auth/login validates credentials, returns user object.' Fields not enumerated.

**Proposed Change:**

Lock the login response to {user_id: uuid, email: string, display_name: string, language_preference: string} with HTTP 200 for success, 401 for invalid credentials.

**Source:** ticket-001 acceptance criteria + contract-002 v1 + your clarifying question

**Frontend Impact (Tweedledee):**

Confirmed. Frontend expects {user_id, email, display_name, language_preference} + 200/401 status. Will store user_id in memory alongside email+password; use user_id in subsequent request paths (POST /conversations/{cid}/messages, etc.). No extra fields needed. Shape is clean and workable.

**Backend Impact (Tweedledum):**

I will implement POST /auth/login to return exactly this shape. No token field, no session field, no extra metadata. Status 200 on valid credentials, 401 on invalid. Stateless per contract-002 v1.

**Resolution:**

Both sides confirmed. Locking contract-note-007 v1: POST /auth/login response shape is {user_id, email, display_name, language_preference} with 200/401 status. Backend implements now; frontend wiring follows.
