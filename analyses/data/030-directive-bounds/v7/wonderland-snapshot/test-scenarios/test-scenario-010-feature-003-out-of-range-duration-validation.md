## Test Scenario: Settings duration values must be validated and rejected if out-of-range

**Severity:** medium

**Feature:** Feature-003 (Customize session and break durations)

**Setup:**

Frontend attempts to PATCH /settings with various out-of-range values:

Request 1: focus_duration_seconds = 60 (below 5-minute minimum)
```json
{ "focus_duration_seconds": 60, "break_duration_seconds": 300 }
```

Request 2: focus_duration_seconds = 7200 (above 60-minute maximum)
```json
{ "focus_duration_seconds": 7200, "break_duration_seconds": 300 }
```

Request 3: break_duration_seconds = 30 (below 1-minute minimum)
```json
{ "focus_duration_seconds": 1500, "break_duration_seconds": 30 }
```

**Trigger:**

Backend receives each PATCH request.

**Expected:**

All three requests return 400 Bad Request with an error message indicating the out-of-range value and the valid range. Examples:
- "focus_duration_seconds must be between 300 and 3600 seconds"
- "break_duration_seconds must be between 60 and 1800 seconds"

Settings are not updated. Previous settings remain unchanged.

**Concern:**

Without server-side validation, a frontend can send invalid durations (via bug, malicious intent, or data corruption). The backend then stores the invalid value, and subsequent sessions use nonsensical durations. For example, a 0-second session would immediately "complete" with no delay, creating confusing UX and false session records.

Additionally, the contract assumes certain bounds. If the backend accepts any value, the frontend's validation is not sufficient (defense in depth).

**Property:**

PATCH /settings must enforce these bounds:
- focus_duration_seconds: 300 to 3600 (5 to 60 minutes)
- break_duration_seconds: 60 to 1800 (1 to 30 minutes)

Any value outside these bounds is rejected with 400 Bad Request. The error message must clearly indicate the expected range.

**Mechanism:**

Backend validation schema (e.g., Pydantic):
```python
class SettingsPatch(BaseModel):
    focus_duration_seconds: int = Field(..., ge=300, le=3600)
    break_duration_seconds: int = Field(..., ge=60, le=1800)
```

**Runnable Tests:**

- `tests/test_feature_003_edge_cases.py::test_feature_003_patch_settings_out_of_range_too_small`
- `tests/test_feature_003_edge_cases.py::test_feature_003_patch_settings_out_of_range_too_large`
- `tests/test_feature_003_edge_cases.py::test_feature_003_patch_settings_break_out_of_range`
