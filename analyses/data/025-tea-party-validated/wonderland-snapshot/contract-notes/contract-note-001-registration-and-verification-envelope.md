## Contract Note 001: Registration and verification envelope

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

POST /register { email, desired_username } → { verification_token_sent: bool, message: string } OR { error: string, suggested_usernames?: [string] }. Verification link in email points to /verify?token=<token>. GET /verify?token=<token> (no auth) returns success redirect or error. After verification, user can log in.

**Source:** ticket-001: user-registration-and-username-claim

**Frontend Impact (Tweedledee):**

Frontend renders registration form (email + username inputs), handles validation errors + suggested alternatives, watches for verification email (external), navigates to login page on success. If user clicks verify link in email, frontend should land them on a 'verified, you can now log in' page or auto-redirect to login. Need to clarify: is verify link a full URL to frontend (with token param) or a backend redirect? Assuming frontend URL for UX clarity.

**Backend Impact (Tweedledum):** _pending_
