## Test Scenario: User exports history with 5000+ sessions, export is truncated

**Severity:** silent-wrongness

**Feature:** Feature-004 (Share session history as proof of effort)

**Setup:**

User has accumulated 5000+ sessions over months of use. Each session is a complete fact in the database, fully recorded. User decides to export their history as proof of work completed.

**Trigger:**

User clicks "export history" button. Frontend calls GET /sessions/export (or POST /sessions/export). Backend queries all sessions for the user and generates an export document.

**Expected:**

Export includes all 5000+ sessions. No sessions are omitted, truncated, or partially recorded. Export is valid JSON (or CSV, or whatever format is chosen) and is complete and importable into other tools (spreadsheet, report generator, etc.).

**Concern:**

Export is truncated at a hard limit (e.g., first 1000 sessions, or buffer size 10MB, or timeout at 30 seconds). Sessions beyond the limit are silently dropped from the export. User exports "proof of effort" but the export is incomplete — showing 1000 sessions when they actually completed 5000. Silent wrongness: the export appears valid, the tool doesn't warn "incomplete," but the exported data is quantitatively wrong. User shares an incomplete export with their manager or teacher, and the proof of effort is understated.

**Property:**

For all users with N sessions, a call to GET /sessions/export must return an export document containing all N sessions, regardless of the value of N (within reasonable hardware limits).

**Implies:**

- Backend may need pagination for very large histories. If pagination is used, the export endpoint must not paginate — it must be either:
  a) A streaming endpoint that sends all sessions as it finds them, or
  b) A batch endpoint that internally handles pagination and assembles the complete result.
  The contract (Feature-004 spec) is ambiguous on this; Tweedles need clarity.

**Runnable Tests:**

- `tests/test_sessions_export_failures.py::TestExportFormat::test_export_includes_all_sessions_in_all_time_window`
- `tests/test_sessions_export_failures.py::TestExportWithLargeHistories::test_export_large_history_is_not_truncated`
- `tests/test_sessions_export_failures.py::TestExportWithLargeHistories::test_export_request_completes_in_reasonable_time`
