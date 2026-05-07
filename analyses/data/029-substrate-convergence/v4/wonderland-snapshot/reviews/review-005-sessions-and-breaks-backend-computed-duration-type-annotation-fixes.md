## Review 005: Sessions and Breaks: Backend-Computed Duration + Type Annotation Fixes

**Files reviewed:** src/backend/api/sessions.py, src/backend/api/breaks.py, src/backend/models.py
**Verdict:** accept

### Approvals

- Type annotations on SessionCreate and BreakCreate now correctly reflect post-validator behavior (datetime, not str). The broken contract is fixed. Future readers will understand the actual field types without confusion.
- Duration validation problem is solved by construction: backend computes duration_seconds = (end_time - start_time).total_seconds() server-side. Client cannot corrupt history; the backend is authoritative on elapsed time. This directly addresses the test concern ('malicious client could corrupt history').
- API surface is cleaner post-change: client sends timestamps and settings snapshot; backend infers duration. Fewer fields the frontend has to calculate and manage. The contract is explicit in the docstrings and coordinated via Contract Note 004 (per pair protocol).
- Immutability, constraint enforcement, and error handling remain intact and correct. The changes are focused—type annotation fix and duration computation—without incidental refactors.

### Cross-domain references

- Contract Note 004 (duration computation, agreed by pair) should be persisted to .wonderland/implementations/ for M6 frontend pair-off reference. Tweedledee will need to know the shape change (duration no longer sent by client).
