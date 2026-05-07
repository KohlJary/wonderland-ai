## Contract Note 002: Authentication token and session envelope

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

POST /login { email, password } → { token: string, user: { username, email } } OR { error: string }. Token is stored client-side (localStorage or HttpOnly cookie — team decision). All authenticated requests include Authorization: Bearer <token> header (or cookie auto-sent). Token has expiry (duration TBD). On token expiry, POST /refresh (with token) → { token: string } OR 401. Logout: POST /logout (with token) → { success: bool }. Invalid/expired tokens return 401 and frontend clears session.

**Source:** ticket-002: user-authentication-and-session-management

**Frontend Impact (Tweedledee):**

Frontend stores token after login. All API requests include Authorization header or cookie. On 401, frontend clears stored token and redirects to login. On refresh token expiry, frontend navigates to login without a refresh loop. Logout endpoint is POST /logout. Need clarity: should refresh token be sent separately or same token refresh twice? Assuming single token with expiry for v1 simplicity.

**Backend Impact (Tweedledum):** _pending_
