## Contract Note 006: Type Annotations: Datetime Post-Validator

**State:** agreed
**Contract Version:** v1-annotation-clarity (SessionCreate.start_time and end_time annotated as datetime post-validator, not str; same for BreakCreate; no change to request/response shapes)

**Current Shape:**

SessionCreate and BreakCreate declare start_time and end_time as str, but the @validator(..., pre=True) decorator converts them to datetime objects post-parsing. Annotation doesn't reflect post-validation type.

**Proposed Change:**

Update SessionCreate.start_time and SessionCreate.end_time annotations from str to datetime (same for BreakCreate). The pre=True validator still accepts str input and converts to datetime; the annotation then correctly documents the type after validation.

**Source:** Caterpillar's review flagged this as a broken contract — annotation claims str but the field contains datetime after parsing. Makes code harder to reason about.

**Frontend Impact (Tweedledee):**

None — this is a backend-side contract clarity fix. My requests still send ISO 8601 strings; the backend still parses them. No change to my request schema.

**Backend Impact (Tweedledum):**

Tweedledum to fill in.

**Resolution:**

agreed. This is a backend-only clarity fix (no frontend impact). Updating annotations to reflect post-validation types improves code readability without changing the request/response contract.
