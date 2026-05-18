"""Tests for env-class verify-failure routing (T-a4).

Verifies the classifier correctly identifies env-class vs code-class
findings, that partitioning works, and that the operator-attention
artifact lands on disk with sensible suggested commands.
"""

from __future__ import annotations

from pathlib import Path

from wonderland.verify_routing import (
    OPERATOR_ATTENTION_DIRNAME,
    EnvAttention,
    FindingClass,
    classify_finding,
    partition_findings,
    record_operator_attention,
    route_verify_findings,
)


# ---------- classifier ----------


def test_modulenotfounderror_classifies_as_env() -> None:
    finding = {
        "title": "pytest collection failed",
        "concern": "ModuleNotFoundError: No module named 'fastapi'",
        "location": "tests/conftest.py:11",
    }
    c = classify_finding(finding)
    assert c.finding_class == FindingClass.ENV
    assert c.captured == "fastapi"


def test_npm_missing_module_classifies_as_env() -> None:
    finding = {
        "title": "npm build failed",
        "concern": "npm ERR! Cannot find module 'react-markdown'",
    }
    c = classify_finding(finding)
    assert c.finding_class == FindingClass.ENV
    assert c.captured == "react-markdown"


def test_pytest_cannot_collect_classifies_as_env() -> None:
    finding = {
        "title": "Test environment missing dependencies",
        "concern": "pytest cannot collect tests",
    }
    c = classify_finding(finding)
    assert c.finding_class == FindingClass.ENV


def test_regular_code_bug_classifies_as_code() -> None:
    finding = {
        "title": "Tag filter does full table scan",
        "concern": (
            "The filter endpoint loads all notes into memory and "
            "filters in Python, defeating the ix_notes_tags index."
        ),
        "location": "src/backend/api/notes.py:147-184",
    }
    c = classify_finding(finding)
    assert c.finding_class == FindingClass.CODE


def test_runtime_error_classifies_as_code() -> None:
    """A runtime bug in app code (OperationalError on a query) is
    code-class even though it has 'Error' in it — the team can fix
    the schema mismatch in the application code."""
    finding = {
        "title": "Schema drift on Session model",
        "concern": (
            "OperationalError: no such column: synced_at — "
            "model declares synced_at but live SQLite doesn't have it."
        ),
        "location": "src/backend/api/sessions.py",
    }
    c = classify_finding(finding)
    # 'OperationalError: no such column' is a code-class problem
    # (model + migration drift; team fixes it) not an env problem
    # (the schema_version table not existing would be env)
    assert c.finding_class == FindingClass.CODE


# ---------- partition ----------


def test_partition_splits_correctly() -> None:
    findings = [
        {"title": "code", "concern": "Bug in handler"},
        {"title": "env", "concern": "ModuleNotFoundError: No module named 'fastapi'"},
        {"title": "another code", "concern": "Off-by-one in pagination"},
        {"title": "another env", "concern": "npm ERR! Cannot find module 'remark-gfm'"},
    ]
    code, env, classes = partition_findings(findings)
    assert len(code) == 2
    assert len(env) == 2
    assert len(classes) == 2
    assert all(c.finding_class == FindingClass.ENV for c in classes)
    assert code[0]["title"] == "code"
    assert env[0]["title"] == "env"


def test_partition_empty_findings_is_safe() -> None:
    code, env, classes = partition_findings([])
    assert code == []
    assert env == []
    assert classes == []


def test_partition_non_dict_items_default_to_code() -> None:
    """Defensive: a non-dict item in the findings list shouldn't
    crash; just routes to code (existing path will skip it)."""
    findings: list = [
        "not-a-dict",
        {"title": "code", "concern": "Bug"},
    ]
    code, env, _ = partition_findings(findings)
    assert len(code) == 2
    assert len(env) == 0


# ---------- operator-attention artifact ----------


def test_record_operator_attention_writes_to_disk(tmp_path: Path) -> None:
    attention = EnvAttention(
        feature_slug="feat-x",
        findings=({"title": "test env missing", "concern": "ModuleNotFoundError: No module named 'fastapi'"},),
        suggested_commands=("uv add --dev fastapi",),
    )
    out_path = record_operator_attention(tmp_path, attention)
    assert out_path.exists()
    assert out_path.parent.name == OPERATOR_ATTENTION_DIRNAME
    body = out_path.read_text()
    assert "feat-x" in body
    assert "uv add --dev fastapi" in body
    assert "Operator attention required" in body


# ---------- end-to-end routing ----------


def test_route_verify_findings_writes_artifact_when_env_present(
    tmp_path: Path,
) -> None:
    findings = [
        {
            "title": "Code bug",
            "concern": "Off-by-one in pagination",
            "location": "src/foo.py",
        },
        {
            "title": "Missing dep",
            "concern": "ModuleNotFoundError: No module named 'fastapi'",
            "location": "tests/conftest.py",
        },
    ]
    code, op_path = route_verify_findings(tmp_path, "feat-x", findings)
    assert len(code) == 1
    assert code[0]["title"] == "Code bug"
    assert op_path is not None
    assert op_path.exists()
    assert "feat-x" in op_path.read_text()
    assert "uv add fastapi" in op_path.read_text()


def test_route_verify_findings_no_artifact_when_all_code(
    tmp_path: Path,
) -> None:
    findings = [
        {"title": "Code bug 1", "concern": "Bug A", "location": "a.py"},
        {"title": "Code bug 2", "concern": "Bug B", "location": "b.py"},
    ]
    code, op_path = route_verify_findings(tmp_path, "feat-x", findings)
    assert len(code) == 2
    assert op_path is None


def test_route_verify_findings_writes_suggested_command(
    tmp_path: Path,
) -> None:
    """The operator-attention artifact's suggested command is the
    operator-facing leverage point. ModuleNotFoundError → uv add."""
    findings = [
        {
            "title": "Missing fastapi",
            "concern": "ModuleNotFoundError: No module named 'fastapi'",
        },
    ]
    code, op_path = route_verify_findings(tmp_path, "feat-x", findings)
    assert op_path is not None
    body = op_path.read_text()
    assert "uv add fastapi" in body
