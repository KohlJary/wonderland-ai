## Contract Note 001: Session persistence API — record shape and core operations

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

None yet; ADR specifies we abstract persistence behind a server-shaped API, but the shape itself is not defined.

**Proposed Change:**

Define the session record schema and the core CRUD operations the frontend will request. Session record includes: id (UUID), startTime (ISO8601), targetDuration (minutes), actualDuration (minutes, null until completion), completionStatus (pending | completed | extended), personaTag (string, optional), breakTaken (boolean), createdAt (ISO8601). Core operations: POST /sessions (create), GET /sessions/{id} (read), PATCH /sessions/{id} (update status/actual duration), GET /sessions?fromDate=X&toDate=Y (query by date range).

**Source:** Ticket 003 (backend persistence design) and tickets 001, 002, 004, 005 (frontend session lifecycle). ADR-002 specifies a server-shaped API; this names the shape.

**Frontend Impact (Tweedledee):**

Frontend will POST to /sessions on initiation, PATCH on completion/extension, GET /sessions with date range filters for daily/weekly/monthly review. UI states depend on this: loading (during API call), pending-sync (queued if offline — deferred to later contract), stale (if local cache diverges from canonical server state). Client state: session timer runs locally; completion status syncs on confirmation.

**Backend Impact (Tweedledum):**

Schema: sessions table (id UUID primary key, startTime, targetDuration INT, actualDuration INT nullable, completionStatus ENUM(pending|completed|extended), personaTag TEXT nullable, breakTaken BOOLEAN default false, createdAt). Backing store: IndexedDB in M1 (client-side only — ADR-002 requirement). Write latency target: <50ms (local IndexedDB typical case). Reads for daily review: index on createdAt for date-range queries (critical for ticket 004). Concurrency: single-user M1 means no concurrent writes expected; if user has app open in multiple tabs, last-write-wins on session completion (acceptable for M1, revisit when multi-user arrives). Error handling: failed write should trap to console + user notification (handled by frontend per UI state rules); invalid updates (e.g., trying to set actualDuration on a pending session with no completion event) are rejected with 400 + reason. Foreign key: completionStatus transitions are state-validated (pending → completed | extended; no backward transitions — this is a history invariant). Query performance target: GET /sessions?fromDate=X&toDate=Y returns < 1000 records in < 200ms (reasonable for v1 session volumes). Schema version field as noted in ticket 003 acceptance: v1 baked into this contract, migrations deferred to later tickets. Not blocking; answer-able from IndexedDB API directly.
