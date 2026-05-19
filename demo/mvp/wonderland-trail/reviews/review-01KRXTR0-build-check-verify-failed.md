## Review 015: Build check (verify) failed

**GUID:** 01KRXTR01S8TCFFDB22NDBQ72J
**Files reviewed:** src/EditorLayout.tsx
**Verdict:** request-changes

### Findings

#### block: Pytest run failed (no parseable failure summary)
**Location:** (test runner did not report a file:line)
**Quote:**

```
Run pytest locally and read the full output to identify what's wrong.

```
............FF..F....                                                    [100%]
=================================== FAILURES
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ``pytest`` exited with code 1 but the output doesn't include a parseable FAILED/ERROR summary line. The suite is broken in a shape this check doesn't recognize.
**Request:** Run pytest locally and read the full output to identify what's wrong.

```
............FF..F....                                                    [100%]
=================================== FAILURES ===================================
_______________ test_post_note_with_duplicate_tag_names_in_list ________________
.venv/lib/python3.13/site-packages/sqlalchemy/engine/base.py:2125: in _exec_insertmany_context
    dialect.do_execute(
.venv/lib/python3.13/site-packages/sqlalchemy/engine/default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlite3.IntegrityError: UNIQUE constraint failed: tags.name

The above exception was the direct cause of the following exception:
tests/test_notes_edge_cases.py:94: in test_post_note_with_duplicate_tag_names_in_list
    res = client.post(
.venv/lib/python3.13/site-packages/starlette/testclient.py:546: in post
    return super().post(
.venv/lib/python3.13/site-packages/httpx/_client.py:1144: in post
    return self.request(
.venv/lib/python3.13/site-packages/starlette/testclient.py:445: in request
    return super().request(
.venv/lib/python3.13/site-packages/httpx/_client.py:825: in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/httpx/_client.py:914: in send
    response = self._send_handling_auth(
.venv/lib/python3.13/site-packages/httpx/_client.py:942: in _send_handling_auth
    response = self._send_handling_redirects(
.venv/lib/python3.13/site-pa

... (truncated for bus payload) ...

nv/lib/python3.13/site-packages/sqlalchemy/engine/default.py:952: in do_execute
    cursor.execute(statement, parameters)
E   sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: tags.name
E   [SQL: INSERT INTO tags (name) VALUES (?) RETURNING id]
E   [parameters: ('foo',)]
E   (Background on this error at: https://sqlalche.me/e/20/gkpj)
_____________ test_delete_note_with_shared_tags_doesnt_orphan_tag ______________
tests/test_notes_edge_cases.py:152: in test_delete_note_with_shared_tags_doesnt_orphan_tag
    assert get2_after.status_code == 200
E   assert 404 == 200
E    +  where 404 = <Response [404 Not Found]>.status_code
_______ test_get_notes_returns_all_notes_in_reverse_chronological_order ________
tests/test_notes_edge_cases.py:231: in test_get_notes_returns_all_notes_in_reverse_chronological_order
    assert notes[0]["id"] == note_id_3
E   assert 1 == 3
=========================== short test summary info ============================
FAILED tests/test_notes_edge_cases.py::test_post_note_with_duplicate_tag_names_in_list
FAILED tests/test_notes_edge_cases.py::test_delete_note_with_shared_tags_doesnt_orphan_tag
FAILED tests/test_notes_edge_cases.py::test_get_notes_returns_all_notes_in_reverse_chronological_order

warning: `VIRTUAL_ENV=/home/jaryk/wonderland-ai/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
```

#### block: Frontend ``npm run build`` failed
**Location:** src/EditorLayout.tsx:18:11
**Quote:**

```
Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App
```

**Read:** The verification runner ``verify`` reports that the implementation in this state cannot run cleanly.
**Concern:** ``npm run build`` exited with code 2. The frontend doesn't build cleanly — could be TypeScript errors, missing imports, an orphaned component (built but never wired into the entry point), or a Vite config mismatch.
**Request:** Run ``npm run build`` locally and fix the errors below. Pay special attention to unresolved imports / missing default exports — the canonical sign that a component shipped but never got wired into App.tsx.

```
src/EditorLayout.tsx(18,11): error TS6196: 'LayoutState' is declared but never used.
src/Preview.tsx(18,23): error TS2307: Cannot find module 'dompurify' or its corresponding type declarations.
src/Preview.tsx(19,24): error TS2307: Cannot find module 'marked' or its corresponding type declarations.
```
