## Contract Note 008: Admin moderation seam (deletion, audit logging)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

no contract yet

**Proposed Change:**

DELETE /admin/user/{username}/homepage (requires admin auth role). Backend: validates request user has admin role, deletes homepage for {username}, logs deletion to audit table { admin_user, target_user, action, timestamp }. Returns { success: bool, deleted_username: string } OR 403 if not admin. Soft-delete option: store deletion in audit table and mark homepage as deleted (returns 404 on public view) but keep original content recoverable. **QUESTION for pair: soft-delete with audit trail vs. hard delete? Affects compliance and rollback.**

**Source:** ticket-008: content-moderation-and-deletion-admin

**Frontend Impact (Tweedledee):**

Admin pages are out of scope for v1 frontend per ticket description (internal endpoint only). If admin UI is added later, it would display user content and trigger deletion via DELETE /admin/user/{username}/homepage. Frontend doesn't render audit logs in v1. **QUESTION: is there a frontend admin dashboard in v1 or is moderation entirely backend/internal for now?** Assuming internal for now.

**Backend Impact (Tweedledum):**

DELETE /admin/homepages/{homepage_id} (admin-only). Admin check: hardcoded admin user list at API layer for v1 (no formal role table yet; can add formal roles later). Deletes homepage (hard-delete v1). Audit logging: new deletion_audits table (id PK, admin_user_id FK, deleted_homepage_id, deleted_user_id, reason nullable, deleted_at). Returns 204. Second DELETE same ID → 404 (idempotent). Invariant: only admins can delete. Failure modes: delete nonexistent homepage → 404; non-admin requests → 403. (Role system design deferred to Cat if formal roles needed; otherwise this API-layer approach works for v1.)
