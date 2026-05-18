"""Env-class verify-failure detection — T-a4.

When ``build_check`` (pytest_collects / pytest_passes / npm_build)
fails, the substrate synthesizes a follow-up ticket and queues it as
Tweedle implementation work. That's correct for code-class failures
(missing imports from local modules, contract drift, runtime bugs)
— but wrong for environment-class failures:

  - Missing dev dependencies in pyproject.toml
  - Missing env vars
  - Missing system packages
  - Broken venv / schema not provisioned

Tweedles can't honestly implement ``install fastapi as a dev dep``
— that's operator/devops work. They either burn budget refusing or
write half-cooked attempts. Mvp-demo F2 surfaced the failure mode:
pytest collection failed on missing ``fastapi``, the substrate
routed it as an implementation ticket, both Tweedles pushed back,
M7+M8 both hit MEETING_BUDGET, loop didn't converge.

This module classifies findings + routes accordingly:

  - **code-class** findings → existing Tweedle ticket-synthesis path
  - **env-class** findings → ``operator_attention`` artifact on disk,
    no Tweedle ticket synthesized

The dashboard surfaces operator_attention items so the operator can
fix the env (one line in pyproject.toml, ``uv add --dev fastapi``,
etc.) before re-queueing the feature.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path

from wonderland.artifact_guid import new_artifact_guid, short_guid

OPERATOR_ATTENTION_DIRNAME = "operator-attention"


class FindingClass(StrEnum):
    """Routing classification for a verify-failure finding."""

    CODE = "code"        # Tweedle implementation work
    ENV = "env"          # Operator / devops work


# Patterns that strongly indicate env-class failures. Conservative —
# we'd rather route a real env issue as code (existing behavior, no
# regression) than route a code issue as env (the operator gets a
# spurious attention item).
_ENV_PATTERNS: list[tuple[FindingClass, re.Pattern[str], str]] = [
    (
        FindingClass.ENV,
        re.compile(
            r"ModuleNotFoundError\s*:\s*No module named\s*['\"]([^'\"]+)['\"]"
        ),
        "missing Python dependency",
    ),
    (
        FindingClass.ENV,
        re.compile(r"ImportError\s*:\s*No module named\s*['\"]?([^'\"\s]+)"),
        "missing Python dependency",
    ),
    (
        FindingClass.ENV,
        re.compile(
            r"\bnpm ERR!\s+Cannot\s+find\s+module\s*['\"]?([^'\"\s]+)"
        ),
        "missing npm dependency",
    ),
    (
        FindingClass.ENV,
        re.compile(r"\bnpm ERR!\s+code\s+E404\b"),
        "npm package not found",
    ),
    (
        FindingClass.ENV,
        re.compile(
            r"missing\s+(?:dev\s+)?dependenc(?:y|ies)?\s+in\s+pyproject",
            re.IGNORECASE,
        ),
        "pyproject.toml missing dependency",
    ),
    (
        FindingClass.ENV,
        re.compile(
            r"\bcommand\s+not\s+found\b|\b: command not found\b",
            re.IGNORECASE,
        ),
        "missing system command",
    ),
    (
        FindingClass.ENV,
        re.compile(
            r"environment\s+missing|env(?:ironment)?\s+(?:setup|setup\s+task)",
            re.IGNORECASE,
        ),
        "environment setup task",
    ),
    (
        FindingClass.ENV,
        re.compile(
            r"pytest\s+cannot\s+collect\s+tests?", re.IGNORECASE,
        ),
        "pytest cannot collect (likely missing deps)",
    ),
]


@dataclass(frozen=True)
class FindingClassification:
    """The classification + a short reason string (for the
    operator_attention artifact body)."""

    finding_class: FindingClass
    reason: str = ""
    captured: str = ""  # the specific module/var/etc. matched, if any


def classify_finding(finding: dict) -> FindingClassification:
    """Classify a single verify-failure finding.

    Returns ``CODE`` by default — env detection has to actively
    match a pattern. Conservative bias prevents false-positive
    operator-attention noise.
    """
    haystacks = [
        str(finding.get("title", "") or ""),
        str(finding.get("location", "") or ""),
        str(finding.get("quote", "") or ""),
        str(finding.get("read", "") or ""),
        str(finding.get("concern", "") or ""),
        str(finding.get("request", "") or ""),
    ]
    blob = "\n".join(haystacks)

    for klass, pattern, reason in _ENV_PATTERNS:
        m = pattern.search(blob)
        if m is not None:
            captured = m.group(1) if m.groups() else ""
            return FindingClassification(
                finding_class=klass, reason=reason, captured=captured,
            )

    return FindingClassification(finding_class=FindingClass.CODE)


@dataclass(frozen=True)
class EnvAttention:
    """Operator-attention payload for env-class verify failures.

    Holds the env-class findings + a best-effort suggested command
    so the dashboard can render a "install fastapi as dev dep" hint
    without operator hunting through traceback output.
    """

    feature_slug: str
    findings: tuple[dict, ...]
    suggested_commands: tuple[str, ...]

    def summary(self) -> str:
        items = "\n".join(
            f"  - **{f.get('title', 'untitled')}** "
            f"@ ``{f.get('location', '?')}``\n"
            f"    Concern: {(f.get('concern') or '')[:200]}"
            for f in self.findings
        ) or "  (none)"
        cmds = "\n".join(
            f"  - ``{c}``" for c in self.suggested_commands
        ) if self.suggested_commands else "  (no automatic suggestion)"
        return (
            f"**Operator attention required: environment-class "
            f"verify failure on feature ``{self.feature_slug}``.**\n\n"
            f"These findings describe env / dependency / tooling "
            f"issues that the Tweedles can't honestly fix — the "
            f"work is operator/devops, not implementation. The "
            f"substrate did NOT synthesize an implementation ticket "
            f"for these (would just burn budget refusing).\n\n"
            f"**Findings:**\n{items}\n\n"
            f"**Suggested operator commands:**\n{cmds}\n\n"
            f"After resolving, re-queue the feature from the "
            f"dashboard to resume implementation."
        )


def _suggest_command(classification: FindingClassification) -> str | None:
    """Best-effort command suggestion based on the classification."""
    if classification.finding_class != FindingClass.ENV:
        return None
    captured = classification.captured.strip() if classification.captured else ""
    reason = classification.reason
    if reason == "missing Python dependency" and captured:
        # Strip submodule path: "fastapi.routing" → "fastapi"
        pkg = captured.split(".", 1)[0]
        return f"uv add {pkg}  # or: uv add --dev {pkg} if test-only"
    if reason == "missing npm dependency" and captured:
        return f"cd frontend && npm install {captured}"
    if reason == "pyproject.toml missing dependency":
        return "uv add <package>  # add the missing dep to pyproject.toml"
    if reason == "pytest cannot collect (likely missing deps)":
        return "uv add --dev pytest fastapi sqlalchemy  # or whatever the imports require"
    return None


def partition_findings(
    findings: list[dict],
) -> tuple[list[dict], list[dict], list[FindingClassification]]:
    """Split findings into (code_class, env_class, env_classifications).

    code_class: pass through to existing Tweedle ticket-synthesis.
    env_class: route to operator_attention.
    env_classifications: parallel list to env_class — same length;
    each carries the classification metadata for the corresponding
    finding (used to build suggested commands).
    """
    code: list[dict] = []
    env: list[dict] = []
    env_classes: list[FindingClassification] = []
    for f in findings:
        if not isinstance(f, dict):
            code.append(f)
            continue
        c = classify_finding(f)
        if c.finding_class == FindingClass.ENV:
            env.append(f)
            env_classes.append(c)
        else:
            code.append(f)
    return code, env, env_classes


def record_operator_attention(
    project_root: Path, attention: EnvAttention,
) -> Path:
    """Persist the operator-attention artifact for the dashboard
    + durable operator-facing record."""
    out_dir = project_root / ".wonderland" / OPERATOR_ATTENTION_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    guid = new_artifact_guid()
    body = (
        f"# Operator attention: {attention.feature_slug}\n\n"
        f"**GUID:** {guid}\n"
        f"**Feature:** {attention.feature_slug}\n"
        f"**Detected at:** {datetime.now(timezone.utc).isoformat()}\n"
        f"**Class:** environment-class verify failure\n\n"
        f"{attention.summary()}\n"
    )
    out_path = out_dir / (
        f"operator-attention-{short_guid(guid)}-{attention.feature_slug}.md"
    )
    out_path.write_text(body, encoding="utf-8")
    return out_path


def route_verify_findings(
    project_root: Path, feature_slug: str, findings: list[dict],
) -> tuple[list[dict], Path | None]:
    """The integration entry point. Returns:

      - ``code_findings``: pass to existing ticket-synthesis path
      - ``operator_attention_path``: where the env-class artifact
        was written, or None if no env findings

    Callers route the code_findings through their existing
    ``_synthesize_followup_ticket_from_finding`` loop and surface
    the operator_attention path to the operator (substrate emits
    a stderr signal; dashboard work to fully surface is a separate
    task).
    """
    code, env, env_classes = partition_findings(findings)
    if not env:
        return code, None

    suggested: list[str] = []
    seen: set[str] = set()
    for c in env_classes:
        cmd = _suggest_command(c)
        if cmd and cmd not in seen:
            seen.add(cmd)
            suggested.append(cmd)

    attention = EnvAttention(
        feature_slug=feature_slug,
        findings=tuple(env),
        suggested_commands=tuple(suggested),
    )
    out_path = record_operator_attention(project_root, attention)
    return code, out_path


__all__ = [
    "FindingClass",
    "FindingClassification",
    "EnvAttention",
    "classify_finding",
    "partition_findings",
    "record_operator_attention",
    "route_verify_findings",
    "OPERATOR_ATTENTION_DIRNAME",
]
