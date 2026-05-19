## Review 006: Build check (verify) failed

**GUID:** 01KRXSJMHFM4XHKWJXG3WQ6DSE
**Files reviewed:** tests/test_notes.py
**Verdict:** request-changes

### Findings

#### block: Test failed: tests/test_notes.py::test_timestamps_iso8601
**Location:** tests/test_notes.py::test_timestamps_iso8601
**Quote:**

```
Run ``pytest tests/test_notes.py::test_timestamps_iso8601`` locally and address the failure. The test names the behavior the code is supposed to deliver.
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** AssertionError: assert ...
**Request:** Run ``pytest tests/test_notes.py::test_timestamps_iso8601`` locally and address the failure. The test names the behavior the code is supposed to deliver.
