## Contract Note 015: Account deletion with cascade

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

DELETE /auth/user (authenticated). Body: {password}. Backend authenticates user (bcrypt verify password), then: (1) mark all sessions for this user as revoked (if we implement revocation; else sessions expire naturally), (2) delete homepage record, (3) delete user record. Return 204 on success. Ask for password to prevent CSRF/accidental deletion.

**Source:** ticket-007

**Frontend Impact (Tweedledee):**

DELETE /user/me {password} from authenticated user. Frontend shows 'Delete Account' button in settings (auth-only page). On click, open modal asking for password confirmation + warning 'this is permanent'. On submit, I POST to /auth/user or /user/me (which endpoint?) with {password}. On 204 success, I clear stored token and redirect to / (home page, unauthenticated). On 401/403 (wrong password), I show error and clear password field. No confirmation email or soft-delete from frontend—the request itself is the confirmation. Question: should I confirm password twice (password + confirm password) or once? Recommend twice (UX pattern). After deletion, user cannot log back in with that email/username (or can they if username becomes available for reuse? You asked this—that's a backend/product call, not frontend impact).

**Backend Impact (Tweedledum):**

Cascade: delete homepages WHERE user_id = ?; delete users WHERE id = ?. Invariant: user record is hard-deleted (not soft-delete). Invariant: after deletion, username becomes available for reuse (question: do we want this?). Invariant: old sessions for deleted user are invalid (either revoked, or expire naturally). Failure mode: delete request arrives while user is editing -> atomic transaction ensures edit is either fully committed or not at all. Failure mode: password verify fails -> reject (401). Question for pair: should we soft-delete with retention period (for regulatory reasons)? Queen may have opinions here. Recommend flagging for her review.
