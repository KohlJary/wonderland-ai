"""Tests for the verification substrate (P16 T-v1).

These tests cover the pure-Python parsing + dispatch surface. The
subprocess paths are exercised by writing tiny self-contained
pyproject.toml + test trees under tmp_path and invoking the real
pytest runner — slow but the only way to catch the integration
between our shell-out and pytest's actual output shape."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from wonderland.verification import (
    VerificationFinding,
    VerificationResult,
    check_pytest_collects,
    check_pytest_passes,
    list_checks,
    register_check,
    run_verification_check,
)


# ---------- skipped-result semantics ----------


def test_no_pyproject_returns_skipped(tmp_path: Path) -> None:
    """A directory without pyproject.toml isn't a Python project —
    the check should bow out gracefully so the substrate doesn't
    start synthesizing tickets for projects that haven't set up
    tests yet."""
    result = check_pytest_collects(tmp_path)
    assert result.ok is False
    assert result.skipped is True
    assert "pyproject.toml" in result.skip_reason
    assert result.findings == ()


def test_no_runner_on_path_returns_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When neither uv nor pytest is available, skip cleanly. The
    substrate treats skipped as informational — no auto-tickets."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\nversion = '0.0.1'\n"
    )
    monkeypatch.setattr(shutil, "which", lambda _: None)
    result = check_pytest_collects(tmp_path)
    assert result.skipped is True
    assert "pytest" in result.skip_reason


# ---------- pytest_collects integration ----------


def _write_minimal_project(
    tmp_path: Path, *, test_body: str = "def test_ok(): assert True\n"
) -> Path:
    """Write a tiny pyproject + tests/ layout under tmp_path so
    pytest can collect against it. Returns the project root."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'verif-fixture'\nversion = '0.0.1'\n"
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("")
    (tmp_path / "tests" / "test_smoke.py").write_text(test_body)
    return tmp_path


@pytest.mark.skipif(
    shutil.which("pytest") is None and shutil.which("uv") is None,
    reason="needs a pytest runner on PATH",
)
def test_collects_passes_on_healthy_project(tmp_path: Path) -> None:
    """A project whose tests import cleanly should pass the
    collection check with ok=True and no findings."""
    project = _write_minimal_project(tmp_path)
    result = check_pytest_collects(project, timeout=30.0)
    assert result.ok is True, result.raw_output
    assert result.findings == ()
    assert result.skipped is False


@pytest.mark.skipif(
    shutil.which("pytest") is None and shutil.which("uv") is None,
    reason="needs a pytest runner on PATH",
)
def test_collects_fails_on_import_error(tmp_path: Path) -> None:
    """A test file that raises at import time should produce a
    finding — this is the class of bug we care most about (the
    ``Depends(get_db)`` shape that passes linters but blows up
    at collection)."""
    project = _write_minimal_project(
        tmp_path,
        test_body=(
            "import nonexistent_package_xyz_definitely_not_real\n"
            "def test_x(): assert True\n"
        ),
    )
    result = check_pytest_collects(project, timeout=30.0)
    assert result.ok is False
    assert result.skipped is False
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert "collection failed" in finding.title.lower()
    assert finding.severity == "block"
    # Raw pytest output should be embedded in the request body so
    # the Tweedles see the exact error.
    assert "nonexistent_package" in finding.request


# ---------- pytest_passes integration ----------


@pytest.mark.skipif(
    shutil.which("pytest") is None and shutil.which("uv") is None,
    reason="needs a pytest runner on PATH",
)
def test_passes_ok_when_tests_pass(tmp_path: Path) -> None:
    project = _write_minimal_project(tmp_path)
    result = check_pytest_passes(project, timeout=60.0)
    assert result.ok is True, result.raw_output


@pytest.mark.skipif(
    shutil.which("pytest") is None and shutil.which("uv") is None,
    reason="needs a pytest runner on PATH",
)
def test_passes_fails_one_finding_per_failed_test(tmp_path: Path) -> None:
    """Two failing tests should produce two findings — one per
    failed test_id — so the substrate can synthesize one ticket
    per concrete failure (matching the existing per-finding-ticket
    behavior on the review side)."""
    project = _write_minimal_project(
        tmp_path,
        test_body=(
            "def test_alpha(): assert 1 == 2\n"
            "def test_beta(): assert False, 'boom'\n"
            "def test_ok(): assert True\n"
        ),
    )
    result = check_pytest_passes(project, timeout=60.0)
    assert result.ok is False
    assert result.skipped is False
    # Two failures → two findings.
    titles = sorted(f.title for f in result.findings)
    assert any("test_alpha" in t for t in titles)
    assert any("test_beta" in t for t in titles)
    # Locations carry the pytest test id format.
    locations = sorted(f.location for f in result.findings)
    assert all("::" in loc for loc in locations)


@pytest.mark.skipif(
    shutil.which("pytest") is None and shutil.which("uv") is None,
    reason="needs a pytest runner on PATH",
)
def test_passes_returns_skipped_when_no_tests_collected(tmp_path: Path) -> None:
    """Pytest exit code 5 = no tests collected. We treat that as
    skipped (a no-tests project hasn't earned a verification
    verdict yet) so the substrate doesn't synthesize tickets
    against an absent suite."""
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'empty'\nversion = '0.0.1'\n"
        "[tool.pytest.ini_options]\ntestpaths = ['tests']\n"
    )
    (tmp_path / "tests").mkdir()
    # No test_*.py files.
    (tmp_path / "tests" / "__init__.py").write_text("")
    result = check_pytest_passes(tmp_path, timeout=30.0)
    assert result.skipped is True
    assert "no tests" in result.skip_reason.lower()


# ---------- dispatcher + registry ----------


def test_run_verification_check_unknown_name_returns_none(tmp_path: Path) -> None:
    """Unknown check name = no-op; same convention as coverage
    checks. Protects against operator typos in YAML."""
    assert run_verification_check("not-a-real-check", tmp_path) is None


def test_list_checks_includes_bundled_checks() -> None:
    names = list_checks()
    assert "pytest_collects" in names
    assert "pytest_passes" in names


def test_register_check_allows_custom_check(tmp_path: Path) -> None:
    """Registry is open — projects can register their own checks
    (e.g. frontend build, type-check) and dispatch through the
    same path."""

    def custom(_root: Path) -> VerificationResult:
        return VerificationResult(check_name="custom_marker", ok=True)

    register_check("custom_marker", custom)
    try:
        result = run_verification_check("custom_marker", tmp_path)
        assert result is not None
        assert result.ok is True
        assert result.check_name == "custom_marker"
    finally:
        # Pop the registration so other tests aren't affected.
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("custom_marker", None)


def test_run_verification_check_catches_check_exceptions(tmp_path: Path) -> None:
    """A crashing check should degrade to skipped, not break the
    workflow run. The substrate's contract is "verification is
    best-effort" — a broken check doesn't get to stop the show."""

    def crasher(_root: Path) -> VerificationResult:
        raise RuntimeError("simulated breakage")

    register_check("crashing_check", crasher)
    try:
        result = run_verification_check("crashing_check", tmp_path)
        assert result is not None
        assert result.skipped is True
        assert "simulated breakage" in result.skip_reason
    finally:
        from wonderland.verification import _CHECK_REGISTRY
        _CHECK_REGISTRY.pop("crashing_check", None)


# ---------- finding shape ----------


def test_finding_severity_defaults_to_block() -> None:
    """Verification failures are objective ticket-worthy regressions;
    default severity matches the routing path's expectations
    (``_TICKETABLE_FINDING_SEVERITIES`` in workflow.py covers
    block + change-required)."""
    f = VerificationFinding(
        title="t", concern="c", request="r",
    )
    assert f.severity == "block"


def test_finding_location_is_optional() -> None:
    """Some failures (esp. early collection errors) don't carry a
    file:line. Empty string is the legal absence value."""
    f = VerificationFinding(title="t", concern="c", request="r")
    assert f.location == ""


# ---------- npm_build (frontend) ----------


from wonderland.verification import (  # noqa: E402
    _has_npm_build_script,
    check_npm_build,
)


def test_npm_detection_returns_none_without_package_json(
    tmp_path: Path,
) -> None:
    """Non-frontend skeletons (python-cli, python-tui, bare
    python-fastapi) have no package.json — frontend check skips."""
    assert _has_npm_build_script(tmp_path) is None


def test_npm_detection_returns_none_when_no_build_script(
    tmp_path: Path,
) -> None:
    """A package.json with no build/typecheck script means there's
    nothing to verify on the frontend side — skip cleanly."""
    (tmp_path / "package.json").write_text(
        '{"name": "x", "scripts": {"test": "echo ok"}}'
    )
    assert _has_npm_build_script(tmp_path) is None


def test_npm_detection_prefers_typecheck_over_build(
    tmp_path: Path,
) -> None:
    """Typecheck is cheaper than full build but covers the most-
    common bug class (TS errors, missing imports). Prefer it when
    available."""
    (tmp_path / "package.json").write_text(
        '{"name": "x", "scripts": {"build": "vite build", '
        '"typecheck": "tsc --noEmit"}}'
    )
    detected = _has_npm_build_script(tmp_path)
    assert detected is not None
    _, script = detected
    assert script == "typecheck"


def test_npm_detection_falls_back_to_build(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"name": "x", "scripts": {"build": "vite build"}}'
    )
    detected = _has_npm_build_script(tmp_path)
    assert detected is not None
    _, script = detected
    assert script == "build"


def test_npm_detection_finds_frontend_subdirectory(tmp_path: Path) -> None:
    """Some skeletons put package.json under ``frontend/`` rather
    than at the project root. Detection walks both."""
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text(
        '{"name": "x", "scripts": {"build": "vite build"}}'
    )
    detected = _has_npm_build_script(tmp_path)
    assert detected is not None
    pkg_dir, _ = detected
    assert pkg_dir == tmp_path / "frontend"


def test_npm_build_skipped_when_no_frontend(tmp_path: Path) -> None:
    """End-to-end skipped path: no package.json → skipped result,
    no findings, no synthesis downstream."""
    result = check_npm_build(tmp_path)
    assert result.skipped is True
    assert result.findings == ()
    assert "frontend" in result.skip_reason.lower()


def test_npm_build_skipped_when_npm_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frontend present but npm not on path = skipped, not failed.
    Operator needs to install Node; not a code defect."""
    (tmp_path / "package.json").write_text(
        '{"name": "x", "scripts": {"build": "vite build"}}'
    )
    monkeypatch.setattr(
        shutil, "which",
        lambda name: None if name == "npm" else shutil.which(name),
    )
    result = check_npm_build(tmp_path)
    assert result.skipped is True
    assert "npm" in result.skip_reason.lower()


@pytest.mark.skipif(
    shutil.which("npm") is None,
    reason="needs npm on PATH",
)
def test_npm_build_passes_on_trivial_script(tmp_path: Path) -> None:
    """A trivial typecheck script that exits 0 should produce ok=True
    and no findings. Uses ``echo`` as the script so we don't need a
    real toolchain installed in the fixture."""
    (tmp_path / "package.json").write_text(
        '{"name": "fixture", "scripts": {"typecheck": "echo ok"}}'
    )
    result = check_npm_build(tmp_path, timeout=30.0)
    assert result.ok is True, result.raw_output
    assert result.findings == ()


@pytest.mark.skipif(
    shutil.which("npm") is None,
    reason="needs npm on PATH",
)
def test_npm_build_fails_with_finding(tmp_path: Path) -> None:
    """A script that exits non-zero should produce a finding with
    severity=block and the runner output embedded for context."""
    (tmp_path / "package.json").write_text(
        '{"name": "fixture", "scripts": '
        '{"typecheck": "echo \\"src/App.tsx:5:12 ERROR: Type \'string\' '
        'is not assignable to \'number\'\\"; exit 1"}}'
    )
    result = check_npm_build(tmp_path, timeout=30.0)
    assert result.ok is False
    assert result.skipped is False
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.severity == "block"
    # Location parser pulls the file:line:col from the output.
    assert "App.tsx:5" in finding.location
