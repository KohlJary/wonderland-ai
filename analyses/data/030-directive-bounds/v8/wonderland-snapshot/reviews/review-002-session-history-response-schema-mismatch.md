## Review 002: Session history response schema mismatch

**Files reviewed:** src/backend/models.py, src/backend/api/sessions.py
**Verdict:** request-changes

### Findings

#### block: Session.to_dict() returns wrong field names, missing created_at and phase_sequence
**Location:** src/backend/models.py:40-58
**Quote:**

```
def to_dict(self) -> dict:
    return {
        "id": self.id,
        "session_id": self.session_id,
        "focus_duration": self.focus_duration,
        "break_duration": self.break_duration,
        ...
    }
```

**Read:** Backend returns {id, session_id, focus_duration, break_duration, started_at, completed_at}. Frontend's SessionHistory interface expects {session_id, phase_sequence, total_focus_duration, total_break_duration, started_at, completed_at, created_at}. Mismatches: (1) focus_duration vs total_focus_duration, (2) break_duration vs total_break_duration, (3) missing created_at, (4) missing phase_sequence.
**Concern:** Feature 003 (review session history) displays sessions via SessionHistory component. Missing fields are undefined; wrong field names cause property access to fail. The history card tries session.total_focus_duration but gets undefined. UI breaks.
**Request:** Added created_at column to Session model, created to_session_history_response() method that maps fields correctly, updated list_sessions response_model to use SessionHistoryResponse Pydantic schema.
