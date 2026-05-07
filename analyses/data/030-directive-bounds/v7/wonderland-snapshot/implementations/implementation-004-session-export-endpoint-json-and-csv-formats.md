## Implementation 004: Session export endpoint (JSON and CSV formats)

**Side:** backend
**Ticket:** 
**Contract:** no explicit contract v (new endpoint, light coverage in M3 notes); implicit contract assumes session list shape matches history-query-shape v1
**Ready for review:** no

**Approach:**

GET /sessions/export?format=json|csv&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD returns session list in requested format. JSON is direct sessions array; CSV is rows with (date, session_id, duration, break_duration, completed_at). Uses same windowing logic as history query.

**Files:**
- src/backend/api/export.py: GET /sessions/export endpoint with format negotiation
- src/backend/api/__init__.py: router registration for export

**Open Questions for Pair:**
- CSV header row locale: always English, or respect user language setting? (Probably out of scope for M5, but flagging.)
- File naming: should export endpoint return Content-Disposition with filename, or does frontend name the download?

**Known Limitations:**
- No streaming for large exports (loads full result set in memory); acceptable for MVP, revisit if exports >10k rows
- CSV format hardcoded; no customization of column selection
