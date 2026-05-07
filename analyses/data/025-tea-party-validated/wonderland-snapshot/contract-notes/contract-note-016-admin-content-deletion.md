## Contract Note 016: Admin content deletion

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

none yet

**Proposed Change:**

DELETE /admin/homepages/{homepage_id} (admin-only). Backend checks admin role, deletes homepage record, logs deletion (who, when, what). Return 204. For v1, scope this to internal API — assume admin is backend operator (not a UI). Moderation queue, user notification, etc. are fast-follow.

**Source:** ticket-008

**Frontend Impact (Tweedledee):**

Admin moderation is out of scope for v1 frontend per the tickets. No admin UI in frontend yet. If/when admin dashboard is added, frontend would render a list of users/homepages and allow delete action, which would POST to DELETE /admin/homepages/{homepage_id} or DELETE /admin/users/{user_id}/homepage. You asked: 'return what was deleted or just 204?' — for v1 (no frontend), doesn't matter. When admin UI arrives (later ticket), you can return 204 and trust the frontend will refetch the list, or return deleted content for confirmation. No preference from frontend standpoint. Audit logging is purely backend concern. Soft vs. hard delete: flagging to the Queen (compliance/retention questions).

**Backend Impact (Tweedledum):**

New table: deletion_audit (id, admin_id FK, deleted_homepage_id, deleted_user_id, reason nullable, deleted_at). Invariant: only admins can delete (role check). Invariant: deletion is hard (no soft-delete for v1, unless Queen mandates audit trail). Failure mode: admin deletes user's homepage, then tries again with same ID -> 404 on second request (idempotent). Question for pair: do we return what was deleted (for confirmation), or just 204? Question: do we need role system before shipping this, or can we gate it at the API layer (request.user_id in hardcoded admin list)?
