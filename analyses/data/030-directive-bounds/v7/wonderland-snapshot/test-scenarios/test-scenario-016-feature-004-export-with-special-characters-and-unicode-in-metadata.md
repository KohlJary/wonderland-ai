## Test Scenario: Export behavior with non-ASCII characters in session metadata

**Severity:** curiosity → degradation (if export is corrupted)

**Feature:** Feature-004 (export history)

**Setup:**

Kenji (export persona) has used the app across multiple locales:
- Some sessions logged from Japan (timestamps in JST, metadata potentially containing Japanese characters)
- Some sessions logged from the US (EST, US locale)
- All within the same user account (single user_id, but varied locale/timezone context)

The app's export feature is called while the device is set to Japanese locale. Kenji exports all-time history to share with a client in the US.

**Trigger:**

GET /sessions/export (or similar endpoint) when the user has sessions with:
- Timestamps in different timezones (JST, EST, UTC)
- Device locale is Japanese (but session timestamps are ISO8601, which is locale-agnostic)
- Export is requested to be in plain-text (per Feature-004's simple text summary format)

**Expected:**

Exported text is correctly encoded (UTF-8 or ASCII-compatible). Timestamps are readable and unambiguous (e.g., "2024-11-18T15:30:00Z" not "18-11-2024 15:30" which is locale-dependent). All session records are included without corruption.

**Concern:**

Unicode and locale-aware formatting can break exports:
1. **Encoding mismatch:** Backend exports as UTF-8, but frontend interprets as ASCII; non-ASCII characters are garbled
2. **Locale-dependent dates:** Backend formats timestamps using the server's locale (e.g., German "18.11.2024") instead of ISO8601; client's locale (Japanese) can't parse it
3. **Emoji or extended characters:** If app ever supports session notes (future feature), emoji in notes break CSV parsing or cause encoding issues
4. **Time zone confusion:** Session completed_at stored as "2024-11-18T15:30:00+09:00" (JST), but export displays it as "2024-11-18T15:30:00" (losing the +09:00, making it ambiguous)

**Property:**

For all session records in an export:
- Timestamps are in ISO8601 format with timezone info (YYYY-MM-DDTHH:MM:SSZ or ±HH:MM offset)
- No locale-dependent date formatting (no "Nov 18" without year, no "18.11.2024" format)
- Character encoding is UTF-8 (or explicitly declared in response headers Content-Type: application/json; charset=utf-8)
- No character loss or corruption even if the export contains non-ASCII text (if session notes are ever added)

**Mechanism:**

Backend should:
1. Store all timestamps in UTC or with explicit timezone info
2. Export timestamps in ISO8601 format (with Z or ±HH:MM offset)
3. Export response must set Content-Type header with charset=utf-8
4. If exporting as JSON, ensure all string fields are properly escaped
5. If exporting as plain text, use UTF-8 encoding and test with non-ASCII characters

**Implies:**

- Dormouse (observability): should monitor export requests with non-ASCII content to catch encoding issues early
- Feature-004 contract may need to specify: "Export timestamps are in ISO8601 format with timezone info; export encoding is UTF-8"
- This scenario is not critical for v1 (app is US-centric, but planning ahead for multi-locale users)

**Runnable Test:**

- `tests/test_feature_004_export_encoding.py::test_export_timestamps_are_iso8601_with_timezone`
- `tests/test_feature_004_export_encoding.py::test_export_is_valid_utf8`
