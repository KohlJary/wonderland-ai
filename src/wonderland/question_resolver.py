"""Automated operator-question resolver (T-ab77).

When an agent fires ``question_to_operator``, the substrate normally
blocks on a human round-trip (600s default). In a fully autonomous run
there is no human — and the ldr-final M2 design receipt showed that, in a
well-specified project, the questions aren't genuine unknowns: all 6 were
**lookups against the milestone roster's done-whens + the directive's
scope-lock**, not product forks. The form's home was declared in M6's
done-when; the resolver's place was fixed by M2's own done-when; story
020/021's milestones were on the roster.

This resolver intercepts the question before the human handler, assembles
grounding context (the full milestone roster + prior answers this run),
and asks a cheap model whether the answer is *derivable from artifacts*:

- **Groundable** → answer autonomously, citing the artifact. No human.
- **Genuine fork** (self-contradictory milestone, true product
  preference the artifacts don't settle) → return None to escalate.

This preserves the Tier-2 contract ("operator as gate-approver only"):
the human is pinged for real decisions, not lookups. Every auto-answer is
tagged ``[auto-resolved …]`` and names its grounding artifact, so a wrong
answer is auditable post-run (the silent-propagation risk mitigation).

Complements the read-milestone tool context (agents self-resolve
ownership inline) and subsumes most of the cross-agent dedup thread
(T-ab75): a resolved answer is published once to the meeting bus.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from wonderland.llm import LLMClient
    from wonderland.workflow import _MilestoneScope


_GOAL_RE = re.compile(
    r"^\*\*Goal:\*\*\s*\n(.*?)(?=^\*\*[A-Z])", re.MULTILINE | re.DOTALL
)
_DONE_WHEN_RE = re.compile(
    r"^\*\*Done when:\*\*\s*\n(.*?)(?=^\*\*[A-Z]|\Z)", re.MULTILINE | re.DOTALL
)


_RESOLVER_SYSTEM = (
    "You are the Wonderland scope resolver — an automated stand-in for the "
    "operator on a fully autonomous design run. An agent has asked the "
    "operator a question. Your job is to decide whether the answer is "
    "DERIVABLE from the project's existing artifacts (the milestone roster's "
    "goals + done-whens, and the operator's prior answers this run), and if "
    "so, to answer it decisively so the team can proceed.\n\n"
    "Rules:\n"
    "- Ownership questions ('which milestone owns surface X — a form, route, "
    "endpoint, card?') are almost always settled by some milestone's "
    "done-when. Find it and answer; name that milestone in your citation.\n"
    "- Scope questions ('does this work belong in the active milestone?') are "
    "settled by the active milestone's own done-when (what it must deliver) "
    "vs other milestones' done-whens (what they own).\n"
    "- Engineering-rhythm questions (decomposition order, all-or-nothing vs "
    "progressive) have no artifact answer — apply a sensible default "
    "(TDD progressive-unblocking; observable outcome as the primary "
    "acceptance condition) and answer; citation='engineering default'.\n"
    "- Be decisive and brief. The operator's answer is a binding contract — "
    "say what to do, then tell them to proceed and compose.\n"
    "- ESCALATE (groundable=false) ONLY for a genuine fork the artifacts "
    "don't settle: a self-contradictory milestone, or a true product "
    "preference with no basis in any done-when. When in real doubt, escalate "
    "— a wrong autonomous answer is worse than one operator round-trip.\n\n"
    "Respond with ONLY a JSON object, no prose around it:\n"
    '{"groundable": true|false, "citation": "<artifact you grounded on>", '
    '"answer": "<decisive answer, empty if escalating>"}'
)


def _extract_section(pattern: re.Pattern[str], text: str) -> str:
    m = pattern.search(text)
    return m.group(1).strip() if m else ""


def build_milestone_roster_context(project_root: Path) -> str:
    """Compact roster of every milestone's slug + name + goal + done-when —
    the grounding the resolver reasons over. Empty string when no roster."""
    from wonderland.milestone import MilestoneRegistry

    registry = MilestoneRegistry(project_root)
    milestones = registry.list_milestones()
    if not milestones:
        return ""
    blocks: list[str] = []
    for m in milestones:
        try:
            body = m.path.read_text(encoding="utf-8")
        except OSError:
            continue
        goal = _extract_section(_GOAL_RE, body)
        done_when = _extract_section(_DONE_WHEN_RE, body)
        block = f"## {m.slug} — {m.name}\nGoal: {goal}\nDone when:\n{done_when}"
        blocks.append(block.strip())
    return "\n\n".join(blocks)


def _parse_resolver_response(text: str) -> dict | None:
    """Parse the resolver's JSON object, tolerating code fences / prose."""
    if not text:
        return None
    # Grab the first {...} block.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(obj, dict) or "groundable" not in obj:
        return None
    return obj


@dataclass(frozen=True)
class QuestionResolution:
    """Outcome of one resolver attempt — for observability + the runner's
    branch. ``answer`` is the tagged operator-answer string when resolved,
    else None (the runner escalates to the human).

    decision values:
      - ``resolved``       — grounded an answer; no human needed.
      - ``escalated``      — genuine fork / not groundable → human.
      - ``no_roster``      — no milestone roster to ground on → human.
      - ``empty_question`` — nothing to resolve → human.
      - ``error``          — resolver/LLM failure → human (best-effort).
    """

    answer: str | None
    decision: str
    citation: str = ""
    latency_ms: float = 0.0


# Forcing function: when an agent has asked this many questions in a
# design run while composing ZERO features, the resolver stops answering
# scope questions and forces composition. M1-resolver receipt: 6 same-
# axis questions, all auto-resolved, 0 features composed — the resolver
# removed the 600s timeout that previously forced progress, so the loop
# became cheap-and-infinite instead of fatal. Answering != forcing.
_FORCE_AFTER_QUESTIONS: int = 2


def _count_features(project_root: Path) -> int:
    """How many features exist on disk — the 'are they composing
    anything?' signal for the forcing function."""
    try:
        from wonderland.feature import FeatureRegistry

        return len(FeatureRegistry(project_root).list_features())
    except Exception:  # noqa: BLE001
        return 0


def _strip_answer_tag(answer: str) -> str:
    """Drop a leading ``[auto-resolved …]`` / ``[…]`` tag to recover the
    answer substance for re-statement in a forcing directive."""
    a = answer.strip()
    if a.startswith("[") and "]" in a:
        return a[a.index("]") + 1 :].strip()
    return a


def _forced_resolution(
    prior_qa: list[tuple[str, str]], n_questions: int, latency_ms: float,
) -> QuestionResolution:
    """Deterministic forcing answer — no LLM call. Re-states the last
    grounded answer's substance + a hard 'compose now, stop asking'
    directive. Also dissolves the story-pool blocker: stories are seeds,
    not a 1:1 spec, so the agent should infer the thin glue a done-when
    implies (e.g. a frontend form) rather than asking for a story that
    frames it."""
    last_substance = (
        _strip_answer_tag(prior_qa[-1][1]) if prior_qa else ""
    )
    answer = (
        f"[auto-resolved — FORCING COMPOSITION] You have asked "
        f"{n_questions} scope questions this design run and composed ZERO "
        f"features. The answer has not changed and will not change: "
        f"{last_substance} "
        f"STOP asking scope questions. The done-when is the contract; the "
        f"stories are SEEDS, not an exhaustive spec — compose features now "
        f"from the available stories and INFER any thin glue the done-when "
        f"implies but no story explicitly frames (e.g. a frontend form for "
        f"an 'end-to-end' flow). Your very next emission MUST be a feature "
        f"decision — a composed feature, not another question, concern, or "
        f"clarification. Proceed and compose."
    )
    return QuestionResolution(
        answer, "forced", citation="forcing-function", latency_ms=latency_ms,
    )


def _format_prior_qa(prior_qa: list[tuple[str, str]]) -> str:
    if not prior_qa:
        return "(none yet this run)"
    return "\n\n".join(
        f"Q: {q.strip()}\nA: {a.strip()}" for q, a in prior_qa
    )


async def resolve_operator_question(
    *,
    project_root: Path,
    scope: "_MilestoneScope | None",
    question: str,
    options: list[str] | None,
    prior_qa: list[tuple[str, str]],
    llm_client: "LLMClient",
    max_tokens: int = 1024,
    clock: "Callable[[], float] | None" = None,
) -> QuestionResolution:
    """Try to answer an operator question from artifacts. Returns a
    ``QuestionResolution``: ``.answer`` is the grounded answer string
    (tagged ``[auto-resolved …]``) when resolved, else None and the
    runner escalates. ``.decision`` records why (resolved / escalated /
    no_roster / empty_question / error) for metrics.
    """
    import time

    _now = clock or time.monotonic
    start = _now()

    def _elapsed() -> float:
        return (_now() - start) * 1000.0

    if not question.strip():
        return QuestionResolution(None, "empty_question", latency_ms=_elapsed())
    roster = build_milestone_roster_context(project_root)
    if not roster:
        return QuestionResolution(None, "no_roster", latency_ms=_elapsed())

    # Forcing function: enough questions, still nothing composed → stop
    # answering scope questions and force a feature decision. Skips the
    # LLM (deterministic + guaranteed forcing language).
    if (
        len(prior_qa) >= _FORCE_AFTER_QUESTIONS
        and _count_features(project_root) == 0
    ):
        return _forced_resolution(prior_qa, len(prior_qa) + 1, _elapsed())

    active_line = (
        f"Active milestone (the one being designed right now): {scope.slug}"
        if scope is not None and scope.slug
        else "Active milestone: (none set)"
    )
    options_line = (
        "Options the agent offered: " + " | ".join(options)
        if options
        else "Options the agent offered: (free-form answer)"
    )
    user = (
        f"{active_line}\n\n"
        f"# Milestone roster\n{roster}\n\n"
        f"# Prior operator answers this run\n{_format_prior_qa(prior_qa)}\n\n"
        f"# The agent's question to the operator\n{question.strip()}\n\n"
        f"{options_line}\n\n"
        "Decide: is the answer derivable from the roster + prior answers? "
        "Respond with the JSON object only."
    )
    try:
        result = await llm_client.complete(
            system=[_RESOLVER_SYSTEM],
            messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens,
        )
    except Exception:  # noqa: BLE001 — resolver failure must not deadlock
        return QuestionResolution(None, "error", latency_ms=_elapsed())
    parsed = _parse_resolver_response(result.text)
    if parsed is None or not parsed.get("groundable"):
        return QuestionResolution(None, "escalated", latency_ms=_elapsed())
    answer = str(parsed.get("answer") or "").strip()
    if not answer:
        return QuestionResolution(None, "escalated", latency_ms=_elapsed())
    citation = str(parsed.get("citation") or "").strip()
    tag = (
        f"[auto-resolved — grounded in: {citation}]"
        if citation
        else "[auto-resolved from milestone roster]"
    )
    return QuestionResolution(
        f"{tag} {answer}", "resolved", citation=citation,
        latency_ms=_elapsed(),
    )


__all__ = [
    "QuestionResolution",
    "resolve_operator_question",
    "build_milestone_roster_context",
]
