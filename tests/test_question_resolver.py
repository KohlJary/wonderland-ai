"""Tests for the automated operator-question resolver (T-ab77).

Uses a fake LLM client returning canned JSON so the grounding +
gate logic is exercised deterministically without an API call.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wonderland.question_resolver import (
    build_milestone_roster_context,
    resolve_operator_question,
)


def _write_milestone(
    project_root: Path, order: int, slug: str, name: str,
    goal: str, done_when: list[str],
) -> None:
    ms_dir = project_root / ".wonderland" / "milestones"
    ms_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"## Milestone {order:02d}: {name}",
        "",
        "**GUID:** 0MST0001",
        f"**Slug:** {slug}",
        f"**Order:** {order}",
        "**Kind:** capability",
        "**Deferred:** false",
        "**Confidence:** high",
        "",
        "**Goal:**",
        "",
        goal,
        "",
        "**Done when:**",
        "",
        *[f"- {d}" for d in done_when],
        "",
    ]
    (ms_dir / f"milestone-0MST00{order:02d}-{slug}.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


class _FakeResult:
    def __init__(self, text: str) -> None:
        self.text = text
        self.stop_reason = "end_turn"
        self.usage = None
        self.raw = None


class _FakeLLM:
    """Records the prompt it was called with; returns canned text."""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.last_user_message: str | None = None

    async def complete(self, *, system, messages, max_tokens=1024):
        self.last_user_message = messages[-1]["content"]
        return _FakeResult(self.response_text)


def _seed_roster(project_root: Path) -> None:
    _write_milestone(
        project_root, 2, "m2-partner-profile-storage", "Partner Profile Storage",
        "Kohl enters Sarah's location once; server resolves to tz + lat/lon.",
        ["POST /partner -> 200 with resolved IANA timezone + lat/lon",
         "partner_profile stored under authenticated user"],
    )
    _write_milestone(
        project_root, 6, "m6-dashboard-integration", "Dashboard Integration",
        "Full dashboard coherent and demo-ready.",
        ["All three cards render together",
         "Partner profile entry form works end-to-end"],
    )


# ---------- grounding context ----------


def test_roster_context_extracts_goal_and_done_when(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    ctx = build_milestone_roster_context(tmp_path)
    assert "m2-partner-profile-storage" in ctx
    assert "POST /partner" in ctx
    assert "Partner profile entry form works end-to-end" in ctx  # M6's done-when


def test_roster_context_empty_when_no_milestones(tmp_path: Path) -> None:
    assert build_milestone_roster_context(tmp_path) == ""


# ---------- resolution ----------


@pytest.mark.asyncio
async def test_groundable_question_returns_tagged_answer(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({
        "groundable": True,
        "citation": "m6-dashboard-integration done-when",
        "answer": "Backend-only. The form is owned by M6.",
    }))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None,
        question="Does M2 include the partner entry form UI?",
        options=None, prior_qa=[], llm_client=llm,
    )
    assert out.decision == "resolved"
    assert out.answer is not None
    assert out.answer.startswith("[auto-resolved")
    assert "m6-dashboard-integration" in out.answer
    assert "Backend-only" in out.answer
    assert out.citation == "m6-dashboard-integration done-when"
    assert out.latency_ms >= 0.0
    # The roster was actually fed to the model.
    assert "Partner profile entry form works end-to-end" in llm.last_user_message


@pytest.mark.asyncio
async def test_escalates_when_not_groundable(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({
        "groundable": False, "citation": "", "answer": "",
    }))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None,
        question="Should the brand color be teal or orange?",
        options=None, prior_qa=[], llm_client=llm,
    )
    assert out.answer is None
    assert out.decision == "escalated"


@pytest.mark.asyncio
async def test_escalates_when_groundable_but_empty_answer(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({
        "groundable": True, "citation": "x", "answer": "   ",
    }))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="Q?",
        options=None, prior_qa=[], llm_client=llm,
    )
    assert out.answer is None
    assert out.decision == "escalated"


@pytest.mark.asyncio
async def test_no_roster_escalates_without_llm_call(tmp_path: Path) -> None:
    llm = _FakeLLM(json.dumps({"groundable": True, "answer": "x", "citation": "y"}))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="Q?",
        options=None, prior_qa=[], llm_client=llm,
    )
    assert out.answer is None
    assert out.decision == "no_roster"
    assert llm.last_user_message is None  # never called the model


@pytest.mark.asyncio
async def test_empty_question_escalates(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM("{}")
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="   ",
        options=None, prior_qa=[], llm_client=llm,
    )
    assert out.answer is None
    assert out.decision == "empty_question"


@pytest.mark.asyncio
async def test_llm_error_escalates(tmp_path: Path) -> None:
    _seed_roster(tmp_path)

    class _BoomLLM:
        last_user_message = None
        async def complete(self, *, system, messages, max_tokens=1024):
            raise RuntimeError("api down")

    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="Q?",
        options=None, prior_qa=[], llm_client=_BoomLLM(),
    )
    assert out.answer is None
    assert out.decision == "error"


@pytest.mark.asyncio
async def test_prior_qa_is_fed_to_resolver(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({"groundable": True, "answer": "ok", "citation": "c"}))
    await resolve_operator_question(
        project_root=tmp_path, scope=None, question="follow-up?",
        options=None,
        prior_qa=[("Is M2 backend only?", "[auto-resolved] Yes, backend only.")],
        llm_client=llm,
    )
    assert "Is M2 backend only?" in llm.last_user_message
    assert "backend only" in llm.last_user_message.lower()


# ---------- runner observability (metrics) ----------


def test_record_question_resolution_writes_jsonl_and_stderr(
    tmp_path: Path, capsys
) -> None:
    """The runner records each resolver decision to a per-run
    question-resolutions.jsonl + a grep-able stderr line, so the A/B
    can count resolved-vs-escalated with citations + latency."""
    from types import SimpleNamespace

    from wonderland.question_resolver import QuestionResolution
    from wonderland.runner import Runner

    stub = SimpleNamespace(project_root=tmp_path, run_id="run-xyz")
    u = SimpleNamespace(
        content=SimpleNamespace(body="Does M2 include the form?"),
        speaker=SimpleNamespace(name="white_rabbit"),
    )
    resolution = QuestionResolution(
        answer="[auto-resolved — grounded in: m6] Backend-only.",
        decision="resolved", citation="m6", latency_ms=42.0,
    )

    Runner._record_question_resolution(stub, u, resolution)

    # stderr breadcrumb
    err = capsys.readouterr().err
    assert "[question-resolver]" in err
    assert "decision=resolved" in err

    # jsonl record
    path = tmp_path / ".wonderland" / "runs" / "run-xyz" / "question-resolutions.jsonl"
    assert path.is_file()
    rec = json.loads(path.read_text().strip())
    assert rec["decision"] == "resolved"
    assert rec["citation"] == "m6"
    assert rec["asking_agent"] == "white_rabbit"
    assert rec["question"] == "Does M2 include the form?"


# ---------- forcing function ----------


def _write_feature(project_root: Path, slug: str, guid: str = "0FEAT001") -> None:
    feat_dir = project_root / ".wonderland" / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    (feat_dir / f"feature-{guid}-{slug}.md").write_text(
        f"## Feature 001: {slug}\n\n**GUID:** {guid}\n**Slug:** {slug}\n"
        f"**Sources:** story-x\n**Stack span:** backend\n\n**Description:**\n\nx\n",
        encoding="utf-8",
    )


@pytest.mark.asyncio
async def test_forces_composition_after_threshold_with_no_features(
    tmp_path: Path,
) -> None:
    """2 prior questions + 0 features composed → force, WITHOUT calling
    the model. This is the M1-resolver loop (6 questions, 0 features)."""
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({"groundable": True, "answer": "x", "citation": "y"}))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None,
        question="M1 done-when wants frontend but I only have backend stories?",
        options=None,
        prior_qa=[
            ("frontend in M1?", "[auto-resolved] Yes, M1 owns the forms."),
            ("really the React forms?", "[auto-resolved] Yes, in M1."),
        ],
        llm_client=llm,
    )
    assert out.decision == "forced"
    assert "FORCING COMPOSITION" in out.answer
    assert "next emission MUST be a feature" in out.answer
    assert "infer" in out.answer.lower()  # dissolves the story-pool blocker
    assert llm.last_user_message is None  # deterministic — no model call


@pytest.mark.asyncio
async def test_does_not_force_when_features_already_composed(
    tmp_path: Path,
) -> None:
    """Same question count, but a feature exists → not a stall; resolve
    normally."""
    _seed_roster(tmp_path)
    _write_feature(tmp_path, "auth-backend")
    llm = _FakeLLM(json.dumps({
        "groundable": True, "answer": "Backend-only.", "citation": "m2",
    }))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="next axis question?",
        options=None,
        prior_qa=[("q1", "a1"), ("q2", "a2")],
        llm_client=llm,
    )
    assert out.decision == "resolved"
    assert llm.last_user_message is not None  # model WAS consulted


@pytest.mark.asyncio
async def test_does_not_force_below_threshold(tmp_path: Path) -> None:
    """One prior question, no features → still under the threshold;
    resolve normally."""
    _seed_roster(tmp_path)
    llm = _FakeLLM(json.dumps({
        "groundable": True, "answer": "ok", "citation": "c",
    }))
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="first follow-up?",
        options=None, prior_qa=[("q1", "a1")], llm_client=llm,
    )
    assert out.decision == "resolved"


@pytest.mark.asyncio
async def test_forced_answer_restates_prior_substance(tmp_path: Path) -> None:
    _seed_roster(tmp_path)
    llm = _FakeLLM("{}")
    out = await resolve_operator_question(
        project_root=tmp_path, scope=None, question="again?",
        options=None,
        prior_qa=[
            ("q1", "a1"),
            ("q2", "[auto-resolved — grounded in: m1] M1 owns the full auth flow."),
        ],
        llm_client=llm,
    )
    assert out.decision == "forced"
    assert "M1 owns the full auth flow." in out.answer  # substance, tag stripped
