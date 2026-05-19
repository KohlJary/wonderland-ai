## Requirement 009: Single-device, single-user, single SQLite file

**GUID:** 01KRXR2J0DSCX2GC81886C2JA3
**Slug:** single-device-single-user-single-sqlite-file
**Kind:** constraint
**Confidence:** operator_stated
**Source interview:** constraints-interview
**Source question:** multi_device_sync

**Body:**

The notebook is bound to one machine. There is no multi-device sync, no cloud backend, no device pairing. The SQLite file is the single source of truth and lives on the user's local filesystem. Deployment is a single instance per user.

**Operator quote:**

> Single device only — one machine, one SQLite file
