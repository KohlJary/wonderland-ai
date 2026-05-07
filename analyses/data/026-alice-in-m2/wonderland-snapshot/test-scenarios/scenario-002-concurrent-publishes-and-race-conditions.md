## Scenario: Two users attempt to publish to the same slug simultaneously (race condition)

**Severity:** breakage

**Setup:**

User A and User B are both authenticated and both own a homepage slug (A owns /~alice, B owns /~bob). A has somehow gained unauthorized access to B's slug (either through a session fixation attack, a permission check bug, or an incorrect authorization header).

Alternatively: A race condition in the slug-allocation logic has resulted in two users being assigned the same slug during concurrent verification operations.

**Trigger:**

User A and User B both issue POST /homepage/bob with different content simultaneously (T=0). Both requests are received by the backend within 10ms of each other. One write completes first, the second write begins and overwrites the first.

**Expected:**

Only one of the writes should succeed. The final state should match the last write that committed. Alternatively, one write should fail with 403 Forbidden (A is not authorized to write to B's slug).

**Concern:**

If the slug-ownership check is not held during the write operation (check-then-act race condition), User A could pass the authorization check at T0 (when A owned the slug), but by T10, A no longer owns the slug (or B has deleted it). The write still goes through and corrupts B's content.

Similarly, if two users somehow share a slug (authorization allocation bug), both can publish and the last write wins, but the authorization boundary is breached.

The breakage is: A user's content is overwritten by someone else, or someone gains unauthorized write access.

**Property:**

For all homepages H and users U, if U is the sole owner of H.slug, then POST /homepage/:slug is atomic: either A is authorized and writes succeed, or A is unauthorized and write fails. No partial writes. No race between authorization check and write.

**Implies:**

Implies a database constraint or transaction boundary — flag for Cat if the implementation uses a naive "check authorization, then write" pattern without holding a lock or using a transaction.

Implies slug-allocation test coverage — if concurrent verification operations can result in duplicate slug allocation, that's a separate scenario.
