## Ticket 069: Backend save endpoint with collision detection and audit trail

**GUID:** 01KRY07VN1CZPAQ1E881BXJF2F
**Sources:** kohl-drafts-and-saves-experimental-notes-with-persistent-backup, story-persistent-backup, story-audit-trail
**Owner:** tweedledum
**Tier:** v1
**Stack span:** backend
**Source:** m3_decomposition
**Test design:** default
**Estimate:** 1.5-2.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: boot-reconciliation-merge
- Blocked by: —
- Soft: —

**Description:**

Implement POST /notes/save endpoint. Accept note id, content, and client-side timestamp. Check for collisions (concurrent saves from different sessions/devices). If collision detected, return conflict marker and both versions. On successful write, record audit trail entry (who, when, what changed). Endpoint returns success + server timestamp + any conflict metadata.

**Acceptance:**
- POST /notes/save accepts note id, content, timestamp
- Collisions are detected and returned with conflict metadata
- Successful saves record audit trail
- Server timestamp is returned for client reconciliation

**Risk:**

Collision detection logic depends on schema design (optimistic locking vs. explicit conflict tables). High risk if schema is still fluid. Recommend confirming schema contract with Caterpillar before starting.
