## Ticket 008: Content moderation and deletion (admin)

**Sources:** moderate-content-or-enforce-community-standards
**Owner:** tweedledum
**Tier:** fast-follow
**Estimate:** 2-3 days, 50% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

Admin-only endpoint to delete or flag user content. Requires design of role system (user vs. admin). Moderators can view reported content, delete, and optionally notify user. This is scoped v1 to 'admin can delete via internal endpoint' — no self-report flow, no moderation queue UI, no email notifications yet. Fast-follow pending architectural clarity on roles.

**Acceptance:**
- Admin endpoint allows deletion of user homepage content
- Admin endpoint logs deletion (who deleted what, when)
- Original content can be audited (soft-delete with retention or audit log)
- Deleted content returns 404 on public view

**Risk:**

Role system not yet designed. Defer to fast-follow unless Cat/Queen surface architectural constraints. If Queen needs audit trails, expand scope to include compliance logging.
