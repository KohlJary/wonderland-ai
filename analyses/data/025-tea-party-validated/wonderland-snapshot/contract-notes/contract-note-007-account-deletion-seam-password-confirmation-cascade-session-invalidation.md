## Contract Note 007: Account deletion seam (password confirmation, cascade, session invalidation)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

DELETE /user/me { password: string } (requires auth). Backend: validates token user is authenticated, validates password is correct for that user, deletes user record + homepage record, invalidates all sessions for that user (mark tokens as revoked or delete from session table). Response: { success: bool } OR { error: string } on validation failure. After successful deletion, user cannot log in again. Frontend should clear token after 204 response.

**Source:** ticket-007: account-deletion-with-content-cascade

**Frontend Impact (Tweedledee):**

Frontend shows 'delete account' button in settings (auth-required page). On click, shows confirmation dialog asking for password confirmation. POSTs to DELETE /user/me with password. On success (204), clears token and redirects to home (or unauthenticated landing). Shows confirmation message. On error: shows error message, keeps password field cleared (for security). No soft-delete from frontend perspective—deletion is immediate.

**Backend Impact (Tweedledum):**

DELETE /auth/user (auth required, JWT). Body: {password}. Validates: (1) JWT user authenticated, (2) password bcrypt-verifies. Atomic transaction: delete homepages WHERE user_id=?; delete users WHERE id=?. Returns 204. Session invalidation: JWT stateless, no server-side revocation; client must discard on success. Hard-delete (no soft-delete for v1; soft-delete is Queen's domain—compliance retention policy TBD). Invariant: username available for reuse after deletion. Failure modes: delete mid-edit → atomic (delete or edit fully commits, not both); password verify fails → 401.
