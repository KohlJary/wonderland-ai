## Contract Note 009: List Notes Endpoint Scope — v1 or v2-fast-follow

**GUID:** 01KRXSMHR0R48BAM2JZ47JPQC0
**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

Schema doc reserves GET /api/notes as v2 fast-follow. Ticket 01KRXRNH accepts it as v1 scope. Implementation contains neither (only POST /notes and GET /notes/{id}). No versioned contract agreement yet.

**Proposed Change:**

Clarify and lock binding authority: Is GET /api/notes part of ticket 01KRXRNH v1 acceptance, or is it genuinely deferred to v2? If v1, move it from 'fast-follow' to 'required' in schema and implement it. If v2, remove it from ticket acceptance and block it until v2 phase.

**Source:** Conflict ticket 01KRXSJ9; review synthesis on ticket 01KRXRNH detected contract/ticket mismatch at SCHEMA.md lines 139–148

**Frontend Impact (Tweedledee):**

[Tweedledee to fill in: depends on whether frontend will call list endpoint in v1 or wait for v2]

**Backend Impact (Tweedledum):**

If v1: requires list-all query with optional pagination (skip/limit), response envelope as per schema lines 154–173. Estimate +0.5 days. If v2: no backend work; current POST/GET {id} suffices.
