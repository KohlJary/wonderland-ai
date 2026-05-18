## Ticket 022: Pytest run failed (no parseable failure summary)

**GUID:** 01KRXTR01YY82BZESV69J35GZ9
**Sources:** kohl-searches-notes-by-title-and-body-content, build-check-verify-failed
**Owner:** tweedledee
**Tier:** v1
**Stack span:** full-stack
**Source:** review_synthesis
**Test design:** default
**Estimate:** tbd — operator should refine
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: —
- Soft: —

**Description:**

From review ``build-check-verify-failed`` (block):

**Concern:** ``pytest`` exited with code 1 but the output doesn't include a parseable FAILED/ERROR summary line. The suite is broken in a shape this check doesn't recognize.

**Request:** Run pytest locally and read the full output to identify what's wrong.

```
.............................................FFF...F...F.....            [100%]
=================================== FAILURES ===================================
____________ test_search_with_percent_sign_as_literal_wildcard_bug _____________
tests/test_search_wildcard_issues.py:48: in test_search_with_percent_sign_as_literal_wildcard_bug
    assert len(data["results"]) == 1, (
E   AssertionError: Expected 1 match for '100%', got 3: ['Other note', '100 percent', '100% complete']. LIKE metacharacter % is not being escaped.
E   assert 3 == 1
E    +  where 3 = len([{'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 3, 'tag_ids': [], ...}, {'body_preview': '', ...2, 'tag_ids': [], ...}, {'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_____________ test_search_with_underscore_as_literal_wildcard_bug ______________
tests/test_search_wildcard_issues.py:82: in test_search_with_underscore_as_literal_wildcard_bug
    assert len(data["results"]) == 1, (
E   AssertionError: Expected 1 match for 'a_b', got 3: ['a1b', 'aXb', 'a_b']. LIKE metacharacter _ is not being escaped.
E   assert 3 == 1
E    +  where 3 = len([{'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 3, 'tag_ids': [], ...}, {'body_preview': '', ...2, 'tag_ids': [], ...}, {'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_______________________ test_search_with_percent_in_body ______________

... (truncated for bus payload) ...

PU: 100% used', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_________________ test_tag_names_with_whitespace_only_entries __________________
tests/test_tag_scenarios.py:33: in test_tag_names_with_whitespace_only_entries
    assert not any(tag.strip() == "" for tag in note["tag_names"])
E   assert not True
E    +  where True = any(<generator object test_tag_names_with_whitespace_only_entries.<locals>.<genexpr> at 0x7882e46a13c0>)
_______________ test_post_associate_tag_with_whitespace_in_name ________________
tests/test_tag_scenarios.py:169: in test_post_associate_tag_with_whitespace_in_name
    assert "  research  " not in note["tag_names"]
E   AssertionError: assert '  research  ' not in ['  research  ']
=========================== short test summary info ============================
FAILED tests/test_search_wildcard_issues.py::test_search_with_percent_sign_as_literal_wildcard_bug
FAILED tests/test_search_wildcard_issues.py::test_search_with_underscore_as_literal_wildcard_bug
FAILED tests/test_search_wildcard_issues.py::test_search_with_percent_in_body
FAILED tests/test_tag_scenarios.py::test_tag_names_with_whitespace_only_entries
FAILED tests/test_tag_scenarios.py::test_post_associate_tag_with_whitespace_in_name

warning: `VIRTUAL_ENV=/home/jaryk/wonderland-ai/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
```

**Location:** ````

**Acceptance:**
- Run pytest locally and read the full output to identify what's wrong.

```
.............................................FFF...F...F.....            [100%]
=================================== FAILURES ===================================
____________ test_search_with_percent_sign_as_literal_wildcard_bug _____________
tests/test_search_wildcard_issues.py:48: in test_search_with_percent_sign_as_literal_wildcard_bug
    assert len(data["results"]) == 1, (
E   AssertionError: Expected 1 match for '100%', got 3: ['Other note', '100 percent', '100% complete']. LIKE metacharacter % is not being escaped.
E   assert 3 == 1
E    +  where 3 = len([{'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 3, 'tag_ids': [], ...}, {'body_preview': '', ...2, 'tag_ids': [], ...}, {'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_____________ test_search_with_underscore_as_literal_wildcard_bug ______________
tests/test_search_wildcard_issues.py:82: in test_search_with_underscore_as_literal_wildcard_bug
    assert len(data["results"]) == 1, (
E   AssertionError: Expected 1 match for 'a_b', got 3: ['a1b', 'aXb', 'a_b']. LIKE metacharacter _ is not being escaped.
E   assert 3 == 1
E    +  where 3 = len([{'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 3, 'tag_ids': [], ...}, {'body_preview': '', ...2, 'tag_ids': [], ...}, {'body_preview': '', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_______________________ test_search_with_percent_in_body ______________

... (truncated for bus payload) ...

PU: 100% used', 'created_at': '2026-05-18T16:28:27.000000Z', 'id': 1, 'tag_ids': [], ...}])
_________________ test_tag_names_with_whitespace_only_entries __________________
tests/test_tag_scenarios.py:33: in test_tag_names_with_whitespace_only_entries
    assert not any(tag.strip() == "" for tag in note["tag_names"])
E   assert not True
E    +  where True = any(<generator object test_tag_names_with_whitespace_only_entries.<locals>.<genexpr> at 0x7882e46a13c0>)
_______________ test_post_associate_tag_with_whitespace_in_name ________________
tests/test_tag_scenarios.py:169: in test_post_associate_tag_with_whitespace_in_name
    assert "  research  " not in note["tag_names"]
E   AssertionError: assert '  research  ' not in ['  research  ']
=========================== short test summary info ============================
FAILED tests/test_search_wildcard_issues.py::test_search_with_percent_sign_as_literal_wildcard_bug
FAILED tests/test_search_wildcard_issues.py::test_search_with_underscore_as_literal_wildcard_bug
FAILED tests/test_search_wildcard_issues.py::test_search_with_percent_in_body
FAILED tests/test_tag_scenarios.py::test_tag_names_with_whitespace_only_entries
FAILED tests/test_tag_scenarios.py::test_post_associate_tag_with_whitespace_in_name

warning: `VIRTUAL_ENV=/home/jaryk/wonderland-ai/.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
```
