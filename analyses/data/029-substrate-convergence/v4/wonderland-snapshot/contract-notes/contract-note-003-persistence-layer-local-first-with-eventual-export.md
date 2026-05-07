## Contract Note 003: Persistence layer: local-first with eventual export

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Not yet defined — stories imply local persistence but export feature (006) is ambiguous about sync vs. one-way download

**Proposed Change:**

v1 and fast-follow features (001–005) use local-only persistence (IndexedDB or localStorage, client-side only). Backend has no involvement. Feature 006 (export/migrate) means: client has a way to export session history as a JSON file or portable format. Export is one-way download, not sync. Backend does not host session data in v1. If post-launch server backing is desired, that's a separate ADR; it would add a sync layer on top of local-first, not replace it.

**Source:** Feature 005 (local-first persistence), Feature 006 (export/migrate), ADR-001 (persistence layer question)

**Frontend Impact (Tweedledee):**

Client-side persistence only for v1. I use IndexedDB to store session records locally (write-once records, queryable by date range for history view). Export is a one-way download: user can click 'export history' and receive a JSON file with all sessions. I don't sync to a server; I don't expect a server endpoint for v1. Migration (Feature 006) would be manual — user exports from device A, imports to device B. If we add server backing later, that's a separate seam and a separate contract note. Cost: manageable — IndexedDB is stable, JSON export is straightforward.

**Backend Impact (Tweedledum):**

You've confirmed — no backend involvement for v1.
