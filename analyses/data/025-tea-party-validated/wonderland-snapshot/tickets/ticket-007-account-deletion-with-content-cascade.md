## Ticket 007: Account deletion (with content cascade)

**Sources:** delete-my-account-and-have-all-my-content-removed
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 0.5-1 day, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: user-authentication-and-session-management
- Soft: —

**Description:**

Authenticated DELETE endpoint for user to delete their own account. On delete: remove user record, remove homepage record, invalidate all sessions for that user. Ask for password confirmation before deletion (security). Return 204 on success. No soft-delete — actually gone.

**Acceptance:**
- Authenticated user can request account deletion
- System prompts for password confirmation
- On confirmation, user record is deleted
- Homepage content is deleted
- All active sessions for that user are invalidated
- User cannot log back in with deleted account
- Other users can still view homepages (should return 404 for deleted user)

**Risk:**

Deletion is permanent. Consider a soft-delete with data retention period before actually deleting, in case Queen has compliance requirements. Flag for her review before shipping.
