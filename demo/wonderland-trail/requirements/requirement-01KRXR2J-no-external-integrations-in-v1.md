## Requirement 010: No external integrations in v1

**GUID:** 01KRXR2J0DSCX2GC81886C2JA4
**Slug:** no-external-integrations-in-v1
**Kind:** constraint
**Confidence:** operator_stated
**Source interview:** constraints-interview
**Source question:** external_connections

**Body:**

The app is self-contained: no filesystem reads/writes beyond SQLite, no clipboard API, no external services (Slack, Obsidian, version control, etc.). All data originates from the user typing into the notebook.

**Operator quote:**

> No external connections for v1
