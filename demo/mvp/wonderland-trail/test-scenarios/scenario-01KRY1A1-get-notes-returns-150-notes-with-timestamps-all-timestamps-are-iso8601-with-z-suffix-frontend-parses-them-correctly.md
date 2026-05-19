## Scenario 287: GET /notes returns 150 notes with timestamps; all timestamps are ISO8601 with Z suffix; frontend parses them correctly

**GUID:** 01KRY1A1CJG4S1VG4H5J0GAQC2
**Severity:** silent-wrongness

**Setup:**

Backend has 150 notes created over 2 weeks. Each has created_at and updated_at timestamps stored in SQLite as naive UTC datetimes. Backend serializes them via ensure_tz_aware() to ISO8601 with Z suffix.

**Trigger:**

Frontend calls GET /api/notes. Backend returns array of NoteResponse objects with {created_at: '2025-05-18T14:30:45.123456Z', updated_at: '2025-05-19T16:20:10.987654Z', ...}.

**Expected:**

Frontend parses each timestamp using Date.parse() or a date library (e.g., date-fns). All timestamps parse successfully. NoteList component renders 'updated' times (e.g., 'Updated 1 hour ago' or 'Updated May 19, 4:20 PM'). Timestamps are accurate relative to current time. No parsing errors, no '1970-01-01' fallback dates, no 'Invalid Date' strings in the UI.

**Concern:**

If the backend returns timestamps in a non-standard format (e.g., Unix epoch, local time without timezone), the frontend's Date.parse() fails and displays 'Invalid Date'. If the frontend doesn't handle microseconds in the ISO8601 string, it might round or truncate incorrectly. If the frontend assumes local timezone instead of UTC, timestamps display in the wrong timezone. Silent wrongness is the UI showing the wrong time to Kohl.

**Property:**

iso8601_utc_timestamps_parse_and_render_correctly_across_frontend_and_backend
