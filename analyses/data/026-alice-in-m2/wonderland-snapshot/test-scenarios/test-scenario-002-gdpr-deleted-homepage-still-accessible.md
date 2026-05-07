## Test Scenario 002: GDPR Deletion — Deleted User's Homepage Still Accessible

**Severity:** breakage

**Setup:**

User kai registers, verifies email, publishes markdown content to /homepage/kai. The homepage is publicly accessible and contains Kai's personal content. Kai then decides to leave the platform and submits a deletion request via account settings.

**Trigger:**

(1) User submits DELETE /auth/delete-account request with password confirmation.
(2) Backend processes deletion (soft-delete user record, cascade to homepage and content).
(3) External actor (attacker, or test) calls GET /homepage/kai.

**Expected:**

GET /homepage/kai returns 404 Not Found. The homepage is no longer accessible. If the actor tries to access the content via JSON format (GET /homepage/kai?format=json), also 404. No error message leaks information about whether the user exists.

**Concern:**

Story-005 (GDPR deletion) specifies: "deletion is immediate (not a 30-day grace period) for GDPR compliance" and "after deletion: homepage is no longer accessible (returns 404)." This is a legal requirement, not an optional feature. If deletion cascades to the user record but the homepage content remains queryable, the system violates GDPR's right to erasure. Users in the EU have the right to have their personal data deleted immediately. A homepage containing published content is personal data; it must be inaccessible post-deletion.

The Dodo's directive names this as "purged (GDPR)" — emphasizing that the requirement is absolute. This scenario is breakage because it's a hard legal boundary: either the system complies with GDPR or it doesn't. There's no in-between.

**Property:**

For all deleted users D with published homepages, GET /homepage/:slug(D) must return 404 immediately after deletion completes. No grace period, no archival, no 'account deleted' message that confirms the account existed.

**Implies:**

- Implies cascade delete logic: DELETE from users WHERE id = ? must cascade to DELETE from homepages WHERE user_id = ? and DELETE from content WHERE homepage_id = ?.
- Implies query logic on GET /homepage/:slug checks whether the homepage owner's account is soft-deleted before returning 200.
- Implies test must verify both immediate deletion (not deferred) and the 404 response (not 410 or 200 with 'account deleted' message).
- Implies audit/compliance: deletion events should be logged (for GDPR audit trails) but user data must not be logged.
