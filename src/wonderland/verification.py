"""Verification checks — substrate primitives that run the shipped
code's own test suite and report structural failures (P16 T-v1).

Where ``coverage.py`` answers "are our artifacts wired" (a design-
time question about milestones consuming requirements, features
realizing them, etc.), ``verification.py`` answers "does the code
we shipped actually load and run." Different question, different
signal, different routing.

A verification check is a pure function ``Path -> VerificationResult``.
The result carries a list of ``VerificationFinding`` instances, each
shaped so it can be lifted directly into a ``ReviewFinding`` and fed
into the existing ``_route_blocking_review`` path in workflow.py —
verification failures synthesize follow-up tickets just like
Caterpillar's blocking findings do today.

Two checks ship in v1:

  - ``pytest_collects`` — run ``pytest --collect-only`` in the
    project root. Collection-time failures (FastAPI dep errors,
    import-time exceptions, syntax errors) surface here. This is
    the cheapest, most-bang-for-buck signal: it catches the
    ``Depends(get_db)`` class of bugs that pass linters but blow
    up at test discovery.

  - ``pytest_passes`` — run ``pytest -q``. Catches actual test
    failures once collection succeeds. Skipped when no tests are
    collected (an empty suite is the collection check's concern,
    not this one's).

Skipped semantics: when no ``pyproject.toml`` lives at the project
root, or no pytest runner is on PATH, the check returns ``ok=False,
skipped=True``. The substrate treats ``skipped=True`` as neither
pass nor fail — informational only, no findings. This is important
for early-phase projects that haven't set up tests yet; we don't
want the substrate to start synthesizing tickets at the operator
just because there's no test infrastructure.

New checks plug in by registering a callable in ``_CHECK_REGISTRY``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# Truncation cap for raw subprocess output that gets embedded in a
# finding's ``request`` field. Pytest tracebacks can be many KB; we
# keep the head so the bus payload stays bounded but the operator
# still gets the actionable detail.
_RAW_OUTPUT_CAP = 3000


@dataclass(frozen=True)
class VerificationFinding:
    """A single verification failure.

    Shape deliberately mirrors a subset of ``wonderland.review.
    ReviewFinding`` so the substrate can lift these into review
    findings without translation. Severity is always ``"block"``
    for verification findings — failing pytest is not a vibe, it's
    a ticket-worthy regression.

    ``title``: noun phrase naming what's broken.
    ``location``: file:line when the runner names one; empty string
        when it doesn't (some collection errors don't carry a path).
    ``concern``: what's wrong and why it matters.
    ``request``: actionable next step. Embeds the relevant raw
        runner output so the Tweedles see the exact error.
    """

    title: str
    concern: str
    request: str
    location: str = ""
    severity: str = "block"


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of one verification check.

    Four shapes the substrate cares about:

      - ``ok=True``: check ran, code is healthy. No findings.
      - ``ok=False, skipped=False``: check ran, code is broken.
        ``findings`` lists what to do about it.
      - ``ok=False, skipped=True``: check didn't run (no test
        infra, no runner binary, etc.). ``skip_reason`` carries
        the operator-friendly explanation. Substrate treats this
        as informational; no synthesis.
      - ``ok=True`` with non-empty findings is not a legal state
        and the dataclass doesn't enforce it; callers should treat
        empty findings as the ok signal.
    """

    check_name: str
    ok: bool
    findings: tuple[VerificationFinding, ...] = ()
    skipped: bool = False
    skip_reason: str = ""
    raw_output: str = ""


# ---------------------------------------------------------------------- #
# Subprocess helpers
# ---------------------------------------------------------------------- #


def _resolve_pytest_command(project_root: Path) -> list[str] | None:
    """Pick the runner to use. Order of preference:

      1. ``uv run pytest`` when a ``pyproject.toml`` exists at the
         project root + uv is on PATH — uv handles dependency
         resolution + project-local venv automatically, which is
         what we want for Wonderland-generated projects (operator
         doesn't have to pre-sync deps).
      2. ``pytest`` on PATH for projects that aren't uv-based.

    Returns the argv prefix to pass to subprocess (without the
    pytest flags), or None when neither is available.

    Earlier version gated on ``uv.lock`` existing — validation3
    pilot revealed the gap: skeleton ships pyproject.toml without
    uv.lock, fallback to bare ``pytest`` runs in Wonderland's venv
    (no fastapi), test collection fails with a missing-deps red
    herring. Switching the trigger to ``pyproject.toml`` + letting
    uv handle the rest moves the dependency-management problem
    from "wonderland operator pre-syncs" to "uv handles
    automatically." Aligned with the npm_build check below, which
    also auto-installs deps before invoking the build."""
    if (project_root / "pyproject.toml").is_file() and shutil.which("uv"):
        # ``--with pytest`` ensures pytest is available even when the
        # project's pyproject.toml doesn't declare it as a dep
        # (skeletons that lean on uv's resolver shouldn't have to
        # repeat "pytest" in their dependencies just to be checked).
        # uv resolves the project deps + pytest into a single env,
        # auto-syncs as needed.
        return ["uv", "run", "--with", "pytest", "pytest"]
    if shutil.which("pytest"):
        return ["pytest"]
    return None


# Pytest emits collection errors in shapes that vary across versions
# but consistently include a ``file.py:NN`` reference somewhere on
# the first error line. This regex grabs the first match; missing
# match = "no location", which is itself useful information.
_PYTEST_LOCATION_RE = re.compile(
    r"([a-zA-Z0-9_/\.\\-]+\.(?:py|tsx?|jsx?|md)):(\d+)"
)


def _extract_first_location(output: str) -> str:
    """Pull the first ``file.py:NN`` reference out of pytest output.
    Returns the matched string, or empty when none found."""
    m = _PYTEST_LOCATION_RE.search(output)
    if not m:
        return ""
    return f"{m.group(1)}:{m.group(2)}"


def _truncate_for_finding(text: str) -> str:
    """Cap subprocess output to bus-friendly size, keeping head +
    tail since pytest typically prints the summary at the bottom."""
    text = text.strip()
    if len(text) <= _RAW_OUTPUT_CAP:
        return text
    head_size = _RAW_OUTPUT_CAP // 2
    tail_size = _RAW_OUTPUT_CAP - head_size - 50
    return (
        text[:head_size]
        + "\n\n... (truncated for bus payload) ...\n\n"
        + text[-tail_size:]
    )


# ---------------------------------------------------------------------- #
# Check 1: pytest_collects
# ---------------------------------------------------------------------- #


def check_pytest_collects(
    project_root: Path,
    *,
    timeout: float = 60.0,
) -> VerificationResult:
    """Run ``pytest --collect-only`` in the project root.

    Returns:
      - ok=True when collection succeeds (any number of tests,
        including zero — that's the pass-check's concern).
      - ok=False, skipped=True when there's no test infrastructure
        to run against.
      - ok=False, findings=[...] when collection actually fails.

    The check is bounded by ``timeout``; timeout itself counts as a
    finding (a code path that hangs at import time is a real bug
    the Tweedles need to address)."""
    if not (project_root / "pyproject.toml").is_file():
        return VerificationResult(
            check_name="pytest_collects",
            ok=False,
            skipped=True,
            skip_reason=(
                "No pyproject.toml at project root — the implementation "
                "phase didn't set up a Python project layout, or the "
                "project is non-Python. Skipping pytest checks."
            ),
        )
    cmd = _resolve_pytest_command(project_root)
    if cmd is None:
        return VerificationResult(
            check_name="pytest_collects",
            ok=False,
            skipped=True,
            skip_reason=(
                "Neither ``uv run pytest`` nor ``pytest`` is available "
                "on the path — install pytest or uv to enable structural "
                "checks."
            ),
        )
    try:
        proc = subprocess.run(
            [*cmd, "--collect-only", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            check_name="pytest_collects",
            ok=False,
            findings=(
                VerificationFinding(
                    title="Pytest collection timed out",
                    concern=(
                        f"``pytest --collect-only`` exceeded {timeout:.0f}s "
                        "before finishing. This usually means an import-"
                        "time block in the project's code — a network "
                        "call at module load, an infinite loop in a "
                        "decorator, or a synchronous wait on something "
                        "that never arrives."
                    ),
                    request=(
                        "Run ``pytest --collect-only`` locally and "
                        "interrupt to see which module is blocking. "
                        "Move blocking work out of import-time paths."
                    ),
                ),
            ),
        )
    if proc.returncode == 0:
        return VerificationResult(
            check_name="pytest_collects",
            ok=True,
            raw_output=_truncate_for_finding(proc.stdout),
        )
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    location = _extract_first_location(combined)
    return VerificationResult(
        check_name="pytest_collects",
        ok=False,
        findings=(
            VerificationFinding(
                title="Pytest collection failed",
                location=location,
                concern=(
                    f"Running ``pytest --collect-only`` exited with code "
                    f"{proc.returncode}. Tests can't be discovered, which "
                    f"typically means a structural bug at module import "
                    f"(missing dependency, framework decorator misuse "
                    f"like FastAPI's ``Depends(get_db)`` left out, "
                    f"syntax error, or an unresolved circular import)."
                ),
                request=(
                    "Read the pytest output below and fix the import-"
                    "time bug. Re-run ``pytest --collect-only`` locally "
                    "to confirm the suite collects.\n\n"
                    f"```\n{_truncate_for_finding(combined)}\n```"
                ),
            ),
        ),
        raw_output=_truncate_for_finding(combined),
    )


# ---------------------------------------------------------------------- #
# Check 2: pytest_passes
# ---------------------------------------------------------------------- #


# Pytest's short test summary lines look like
#   FAILED tests/test_foo.py::test_bar - AssertionError: ...
# This regex pulls the test id and the failure summary out of one
# such line.
_PYTEST_FAILED_LINE_RE = re.compile(
    r"^FAILED\s+(\S+::\S+)\s*-\s*(.+)$",
    re.MULTILINE,
)
_PYTEST_ERROR_LINE_RE = re.compile(
    r"^ERROR\s+(\S+(?:::\S+)?)\s*-\s*(.+)$",
    re.MULTILINE,
)


def _parse_pytest_failures(output: str) -> list[VerificationFinding]:
    """Pull FAILED + ERROR lines from pytest's summary section into
    individual findings. Each failure becomes one finding with the
    test id as the title and the summary line as the concern."""
    findings: list[VerificationFinding] = []
    for m in _PYTEST_FAILED_LINE_RE.finditer(output):
        test_id, summary = m.group(1), m.group(2).strip()
        findings.append(
            VerificationFinding(
                title=f"Test failed: {test_id}",
                location=test_id,
                concern=summary,
                request=(
                    f"Run ``pytest {test_id}`` locally and address the "
                    f"failure. The test names the behavior the code is "
                    f"supposed to deliver."
                ),
            )
        )
    for m in _PYTEST_ERROR_LINE_RE.finditer(output):
        test_id, summary = m.group(1), m.group(2).strip()
        findings.append(
            VerificationFinding(
                title=f"Test errored: {test_id}",
                location=test_id,
                concern=(
                    f"The test couldn't even run: {summary}. "
                    f"Setup/fixture/import failure that prevents the "
                    f"assertion from being evaluated."
                ),
                request=(
                    f"Run ``pytest {test_id}`` locally and address the "
                    f"setup error. Fixture-level failures usually "
                    f"point at conftest.py or the test module's imports."
                ),
            )
        )
    return findings


def check_pytest_passes(
    project_root: Path,
    *,
    timeout: float = 180.0,
) -> VerificationResult:
    """Run ``pytest -q`` in the project root.

    Returns:
      - ok=True when every test passes (or when zero tests ran —
        that's collection's concern).
      - ok=False, skipped=True when test infrastructure is absent.
      - ok=False, findings=[...] one per failed/errored test.
    """
    if not (project_root / "pyproject.toml").is_file():
        return VerificationResult(
            check_name="pytest_passes",
            ok=False,
            skipped=True,
            skip_reason="No pyproject.toml at project root.",
        )
    cmd = _resolve_pytest_command(project_root)
    if cmd is None:
        return VerificationResult(
            check_name="pytest_passes",
            ok=False,
            skipped=True,
            skip_reason="Neither uv nor pytest is on PATH.",
        )
    try:
        proc = subprocess.run(
            [*cmd, "-q", "--tb=short", "--no-header"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            check_name="pytest_passes",
            ok=False,
            findings=(
                VerificationFinding(
                    title="Pytest run timed out",
                    concern=(
                        f"``pytest`` exceeded {timeout:.0f}s before "
                        "finishing. A test (or its fixture) is hanging."
                    ),
                    request=(
                        "Run pytest locally with ``-x`` to stop at the "
                        "first hung test. Investigate the fixture / "
                        "test body for unbounded waits."
                    ),
                ),
            ),
        )
    if proc.returncode == 0:
        return VerificationResult(
            check_name="pytest_passes",
            ok=True,
            raw_output=_truncate_for_finding(proc.stdout),
        )
    # Pytest exit code 5 means "no tests collected" — for our
    # purposes that's a skip, not a failure (collection check
    # will surface the same thing as ok=True with zero tests).
    if proc.returncode == 5:
        return VerificationResult(
            check_name="pytest_passes",
            ok=False,
            skipped=True,
            skip_reason=(
                "No tests were collected — pytest exit code 5. The "
                "project shipped without runnable tests; the test-"
                "scenarios catalog hasn't been wired into actual "
                "test functions yet."
            ),
            raw_output=_truncate_for_finding(proc.stdout),
        )
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    findings = tuple(_parse_pytest_failures(combined))
    if not findings:
        # Pytest exited non-zero but we couldn't parse a specific
        # failure summary. Surface the raw output as a single
        # finding so the operator at least sees the signal.
        findings = (
            VerificationFinding(
                title="Pytest run failed (no parseable failure summary)",
                concern=(
                    f"``pytest`` exited with code {proc.returncode} but "
                    f"the output doesn't include a parseable FAILED/"
                    f"ERROR summary line. The suite is broken in a "
                    f"shape this check doesn't recognize."
                ),
                request=(
                    "Run pytest locally and read the full output to "
                    "identify what's wrong.\n\n"
                    f"```\n{_truncate_for_finding(combined)}\n```"
                ),
            ),
        )
    return VerificationResult(
        check_name="pytest_passes",
        ok=False,
        findings=findings,
        raw_output=_truncate_for_finding(combined),
    )


# ---------------------------------------------------------------------- #
# Check 3: npm_build (frontend)
# ---------------------------------------------------------------------- #


def _has_npm_build_script(project_root: Path) -> tuple[Path, str] | None:
    """Detect whether the project has a runnable frontend build.

    Returns ``(package_json_dir, script_name)`` when a build is wired
    up, or None when the skeleton doesn't make sense for a frontend
    check (no package.json, or one without a ``build``/``typecheck``
    script). Frontend-less skeletons (python-cli, python-tui,
    python-fastapi without a paired React app) skip cleanly via the
    None return.

    Looks at the project root first, then a ``frontend/`` subdirectory
    — the two layouts Wonderland's skeletons use today. Picks
    ``typecheck`` over ``build`` when both exist: typecheck is cheaper
    and surfaces the most-common class of bug (TypeScript errors,
    missing imports, orphaned components) without the bundler step.
    """
    import json

    candidate_dirs = (project_root, project_root / "frontend")
    for d in candidate_dirs:
        pkg = d / "package.json"
        if not pkg.is_file():
            continue
        try:
            data = json.loads(pkg.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scripts = data.get("scripts", {})
        if not isinstance(scripts, dict):
            continue
        # Preferred order: typecheck (cheap) → build (full).
        for script in ("typecheck", "type-check", "build"):
            if script in scripts:
                return d, script
    return None


# TypeScript / vite errors emit ``file.ts(line,col): error TSnnnn:`` or
# ``src/foo.tsx:line:col: ERROR`` shapes. This regex covers both.
_TS_LOCATION_RE = re.compile(
    r"([a-zA-Z0-9_/\.\\-]+\.(?:tsx?|jsx?|vue|svelte))"
    r"[(:](\d+)[,:](\d+)?"
)


def check_npm_build(
    project_root: Path,
    *,
    timeout: float = 180.0,
) -> VerificationResult:
    """Run the project's frontend build (or typecheck) script.

    Returns:
      - ok=True when the build succeeds.
      - ok=False, skipped=True when the project has no frontend
        infrastructure (no package.json with a build/typecheck
        script). Frontend-less skeletons skip here.
      - ok=False, findings=[...] when the build fails. Findings
        carry file:line:col when the build's output names a
        location, else just the script's output.
    """
    detected = _has_npm_build_script(project_root)
    if detected is None:
        return VerificationResult(
            check_name="npm_build",
            ok=False,
            skipped=True,
            skip_reason=(
                "No package.json with a ``typecheck``/``build`` "
                "script found at project root or frontend/ — skeleton "
                "doesn't have a frontend to build."
            ),
        )
    pkg_dir, script_name = detected
    if shutil.which("npm") is None:
        return VerificationResult(
            check_name="npm_build",
            ok=False,
            skipped=True,
            skip_reason="npm not on PATH — install Node.js to enable frontend checks.",
        )

    # Ensure dependencies are installed before invoking the build.
    # validation3 pilot revealed the failure mode: skeletons ship a
    # package.json without ``node_modules`` — fresh ``npm run build``
    # then fails with "Cannot find module 'react'" even though the
    # frontend code is healthy. Auto-install bridges the gap; the
    # build check then surfaces real build errors instead of
    # missing-deps noise. ``npm ci`` is preferred (clean reproducible
    # install from lockfile) when ``package-lock.json`` exists;
    # otherwise fall back to ``npm install``. Install timeout is
    # generous since pulling deps is bounded by network not CPU.
    if not (pkg_dir / "node_modules").is_dir():
        install_cmd = (
            ["npm", "ci", "--silent"]
            if (pkg_dir / "package-lock.json").is_file()
            else ["npm", "install", "--silent"]
        )
        try:
            install_proc = subprocess.run(
                install_cmd,
                cwd=pkg_dir,
                capture_output=True,
                text=True,
                timeout=300.0,
            )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                check_name="npm_build",
                ok=False,
                findings=(
                    VerificationFinding(
                        title=f"Frontend ``{' '.join(install_cmd)}`` timed out",
                        concern=(
                            f"Dependency install exceeded 300s. Likely a "
                            f"network problem or a postinstall script "
                            f"hanging. Build can't run without deps."
                        ),
                        request=(
                            f"Run ``{' '.join(install_cmd)}`` locally to "
                            f"see what's stalling."
                        ),
                    ),
                ),
            )
        if install_proc.returncode != 0:
            combined = (
                install_proc.stdout + "\n" + install_proc.stderr
            ).strip()
            return VerificationResult(
                check_name="npm_build",
                ok=False,
                findings=(
                    VerificationFinding(
                        title=f"Frontend ``{' '.join(install_cmd)}`` failed",
                        concern=(
                            f"Dependency install exited with code "
                            f"{install_proc.returncode}. Likely a package "
                            f"resolution failure (incompatible peer deps, "
                            f"unpublished version, registry timeout) or a "
                            f"postinstall script crash. Build can't run "
                            f"without deps."
                        ),
                        request=(
                            f"Run ``{' '.join(install_cmd)}`` locally and "
                            f"fix the install error below.\n\n"
                            f"```\n{_truncate_for_finding(combined)}\n```"
                        ),
                    ),
                ),
                raw_output=_truncate_for_finding(combined),
            )
    try:
        proc = subprocess.run(
            ["npm", "run", script_name, "--silent"],
            cwd=pkg_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            check_name="npm_build",
            ok=False,
            findings=(
                VerificationFinding(
                    title=f"Frontend ``npm run {script_name}`` timed out",
                    concern=(
                        f"Build exceeded {timeout:.0f}s. Likely a "
                        f"webpack/vite hang, a circular type import, "
                        f"or a postinstall script that never returns."
                    ),
                    request=(
                        f"Run ``npm run {script_name}`` locally to "
                        f"interrupt and inspect."
                    ),
                ),
            ),
        )
    if proc.returncode == 0:
        return VerificationResult(
            check_name="npm_build",
            ok=True,
            raw_output=_truncate_for_finding(proc.stdout),
        )
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    # Try to pull file:line context out for the location field; pick
    # the first concrete TS/JSX path we see.
    location = ""
    m = _TS_LOCATION_RE.search(combined)
    if m:
        location = f"{m.group(1)}:{m.group(2)}"
        if m.group(3):
            location += f":{m.group(3)}"
    return VerificationResult(
        check_name="npm_build",
        ok=False,
        findings=(
            VerificationFinding(
                title=f"Frontend ``npm run {script_name}`` failed",
                location=location,
                concern=(
                    f"``npm run {script_name}`` exited with code "
                    f"{proc.returncode}. The frontend doesn't build "
                    f"cleanly — could be TypeScript errors, missing "
                    f"imports, an orphaned component (built but never "
                    f"wired into the entry point), or a Vite config "
                    f"mismatch."
                ),
                request=(
                    f"Run ``npm run {script_name}`` locally and fix "
                    f"the errors below. Pay special attention to "
                    f"unresolved imports / missing default exports — "
                    f"the canonical sign that a component shipped "
                    f"but never got wired into App.tsx.\n\n"
                    f"```\n{_truncate_for_finding(combined)}\n```"
                ),
            ),
        ),
        raw_output=_truncate_for_finding(combined),
    )


# ---------------------------------------------------------------------- #
# Registry
# ---------------------------------------------------------------------- #


CheckFn = Callable[[Path], VerificationResult]


_CHECK_REGISTRY: dict[str, CheckFn] = {
    "pytest_collects": check_pytest_collects,
    "pytest_passes": check_pytest_passes,
    "npm_build": check_npm_build,
}


def run_verification_check(
    check_name: str,
    project_root: Path,
) -> VerificationResult | None:
    """Dispatch into the registered check. Returns None for unknown
    check names (operator typo in YAML degrades to no-op, same
    convention as ``coverage.run_coverage_check``). Catches all
    runner exceptions and converts them to a skipped result so a
    crashing check doesn't break the workflow run."""
    fn = _CHECK_REGISTRY.get(check_name)
    if fn is None:
        return None
    try:
        return fn(project_root)
    except Exception as exc:  # noqa: BLE001 — verification is best-effort
        return VerificationResult(
            check_name=check_name,
            ok=False,
            skipped=True,
            skip_reason=f"Check crashed: {type(exc).__name__}: {exc}",
        )


def register_check(name: str, fn: CheckFn) -> None:
    """Plug a new verification check into the registry. Used by
    tests and future extensions (frontend builds, type checks)."""
    _CHECK_REGISTRY[name] = fn


def list_checks() -> list[str]:
    """Names of every registered check. For CLI / docs."""
    return sorted(_CHECK_REGISTRY.keys())
