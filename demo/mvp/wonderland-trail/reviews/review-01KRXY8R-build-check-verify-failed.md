## Review 027: Build check (verify) failed

**GUID:** 01KRXY8R84QAK300H9D2F89WZA
**Files reviewed:** src/Preview.tsx
**Verdict:** request-changes

### Findings

#### block: Pytest run failed (no parseable failure summary)
**Location:** (test runner did not report a file:line)
**Quote:**

```
Run pytest locally and read the full output to identify what's wrong.

```
.............................................F...F.....                  [100%]
=================================== FAILURES
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ``pytest`` exited with code 1 but the output doesn't include a parseable FAILED/ERROR summary line. The suite is broken in a shape this check doesn't recognize.
**Request:** Run pytest locally and read the full output to identify what's wrong.

```
.............................................F...F.....                  [100%]
=================================== FAILURES ===================================
_________________ test_tag_names_with_whitespace_only_entries __________________
tests/test_tag_scenarios.py:33: in test_tag_names_with_whitespace_only_entries
    assert not any(tag.strip() == "" for tag in note["tag_names"])
E   assert not True
E    +  where True = any(<generator object test_tag_names_with_whitespace_only_entries.<locals>.<genexpr> at 0x7632a0d4b440>)
_______________ test_post_associate_tag_with_whitespace_in_name ________________
tests/test_tag_scenarios.py:169: in test_post_associate_tag_with_whitespace_in_name
    assert "  research  " not in note["tag_names"]
E   AssertionError: assert '  research  ' not in ['  research  ']
=========================== short test summary info ============================
FAILED tests/test_tag_scenarios.py::test_tag_names_with_whitespace_only_entries
FAILED tests/test_tag_scenarios.py::test_post_associate_tag_with_whitespace_in_name

warning: `VIRTUAL_ENV=/home/jaryk/wonderland-ai/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
```

#### block: Frontend ``npm run build`` failed
**Location:** src/Preview.tsx:18:23
**Quote:**

```
Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ``npm run build`` exited with code 2. The frontend doesn't build cleanly — could be TypeScript errors, missing imports, an orphaned component (built but never wired into the entry point), or a Vite config mismatch.
**Request:** Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App.tsx.

```
src/Preview.tsx(18,23): error TS2307: Cannot find module 'dompurify' or its corresponding type declarations.
src/Preview.tsx(19,24): error TS2307: Cannot find module 'marked' or its corresponding type declarations.
```
