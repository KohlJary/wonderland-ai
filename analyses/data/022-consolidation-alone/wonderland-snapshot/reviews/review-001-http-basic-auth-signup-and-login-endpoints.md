## Review 001: HTTP Basic Auth: signup and login endpoints

**Files reviewed:** src/backend/models.py, src/backend/auth.py, src/backend/api/auth.py, src/backend/api/__init__.py
**Verdict:** accept

### Approvals

- Error handling on parse_basic_auth is correct: rejects malformed headers with 401 and WWW-Authenticate header, does not expose email existence via timing attack.
- Password hashing via argon2 is solid; verify_password is correctly delegated to passlib (timing-safe comparison).
- Database invariants are well-named and enforced: User.email is unique + indexed; password_hash is non-nullable; language_preference defaults to 'en'.
- UserResponse shape matches contract-note-002 v1 exactly (user_id, email, display_name, language_preference); to_dict() mapping is explicit and correct.
- Signup validation is appropriate: language_preference is validated against a known-good set (expandable); duplicate email is caught at DB constraint and reported as 400 with clear message.
- The router is correctly wired into api/__init__.py at the root path (not nested under /api prefix), matching contract-002's POST /auth/signup and POST /auth/login.
- Docstrings name the contract being implemented (Contract-002 v1) and state the invariants being enforced. Future readers have a clear reference.

### Cross-domain references

- Tweedledee: you can now wire frontend auth UI (email+password storage, Authorization: Basic header injection) against this contract. The shape is locked; build to it.
- Tweedledee's question about conversation_id and message_id generation is architectural—Cat should advise. My read: client-generated UUIDs (in contract-note-001's message_send spec?) or server-generated IDs. The User model doesn't imply the answer; contract-note-001 should clarify.
