## Ticket 015: Schema doc reserves list endpoint for v2, contradicting ticket scope

**GUID:** 01KRXSJ9M9FJE2AFDNNFFW8BJB
**Sources:** kohl-can-create-and-save-experimental-notes-with-title-and-body, backend-note-and-tag-crud-endpoints
**Owner:** tweedledee
**Tier:** v1
**Stack span:** full-stack
**Source:** review_synthesis
**Test design:** skip
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``backend-note-and-tag-crud-endpoints`` (change-required):

**Concern:** The contract document and the ticket scope are in conflict. If GET /api/notes is deferred to v2, the ticket acceptance criteria should not require it for v1. If it's v1 scope, the schema doc should not mark it as fast-follow. This ambiguity will cause triage problems downstream (frontend blocked waiting for the endpoint, or confused about when it actually ships).

**Request:** Clarify with the Cat (who owns the contract via the SCHEMA.md document) and the Rabbit (who owns the ticket scope) which is binding. Update one artifact to match the other. If the endpoint is genuinely deferred, remove it from ticket acceptance. If it's v1 scope, move it from 'fast-follow' to 'required' in the schema and implement it.

**Location:** ``docs/SCHEMA.md, lines 139-148``

**Acceptance:**
- Clarify with the Cat (who owns the contract via the SCHEMA.md document) and the Rabbit (who owns the ticket scope) which is binding. Update one artifact to match the other. If the endpoint is genuinely deferred, remove it from ticket acceptance. If it's v1 scope, move it from 'fast-follow' to 'required' in the schema and implement it.
