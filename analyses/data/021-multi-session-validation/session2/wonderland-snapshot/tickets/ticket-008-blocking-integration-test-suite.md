## Ticket 008: Blocking integration test suite

**Sources:** story: block-a-user-who-is-bothering-me, story: know-a-blocked-message-didn-t-reach-me, story: unblock-someone-and-resume-contact
**Owner:** mad_hatter
**Tier:** v1
**Estimate:** 0.5–1 day, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: blocking-endpoints-post-get-delete-blocks
- Soft: —

**Description:**

Test scenarios for blocking: (1) blocker creates block, blocked user cannot send message (403); (2) blocked user cannot see messages sent after block (list returns 200 with empty array); (3) blocked user CAN see messages sent before block (if any); (4) unblock restores visibility; (5) block is unidirectional (blocked user can still send message to blocker if blocker has not also blocked them); (6) duplicate block is idempotent; (7) delete after unblock is idempotent. Severity: all blocking scenarios are high-severity (safety-critical feature).

**Acceptance:**
- All seven scenarios pass
- Severity: high on all scenarios
- Edge cases covered: (a) block then message sent in quick succession; (b) unblock then message sent in quick succession; (c) bidirectional blocks

**Risk:**

Race conditions during concurrent block/unblock/message-send may expose timing issues. Expand to 1.5 days if gate logic requires transaction wrapping (see prior ticket risk).
