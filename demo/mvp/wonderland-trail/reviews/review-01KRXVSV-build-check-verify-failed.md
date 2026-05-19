## Review 019: Build check (verify) failed

**GUID:** 01KRXVSVW7J5P6RS1J21D01S3X
**Files reviewed:** src/Preview.tsx, tests/test_search.py
**Verdict:** request-changes

### Findings

#### block: Test failed: tests/test_search.py::test_tag_filtering_with_multiple_tag_names
**Location:** tests/test_search.py::test_tag_filtering_with_multiple_tag_names
**Quote:**

```
Run ``pytest tests/test_search.py::test_tag_filtering_with_multiple_tag_names`` locally and address the failure. The test names the behavior the code is supposed to deliver.
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ass...
**Request:** Run ``pytest tests/test_search.py::test_tag_filtering_with_multiple_tag_names`` locally and address the failure. The test names the behavior the code is supposed to deliver.

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
src/Search.tsx(57,10): error TS6133: 'apiQuery' is declared but its value is never read.
src/Search.tsx(58,10): error TS6133: 'apiTags' is declared but its value is never read.
```
