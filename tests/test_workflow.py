"""Tests for wonderland.workflow — schema, loader, and execution.

Covers the data-on-disk workflow substrate plus run_workflow against
a fake Runner. Real-runner integration is exercised by the showcase
scripts (smoke-tested with live API).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from wonderland.utterance import (
    AgentIdentity,
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)
from wonderland.workflow import (
    Meeting,
    MeetingEndEvent,
    MeetingStartEvent,
    SeedBinding,
    Workflow,
    WorkflowCapture,
    WorkflowDefaults,
    list_workflows,
    load_workflow,
    resolve_seeds,
    run_workflow,
    workflows_dir,
)


# ---------------------------------------------------------------------------
# Helpers — minimal Utterance + Artifact builders for fixture data
# ---------------------------------------------------------------------------


def _utt(
    *,
    thread_id: str,
    speaker: str = "alice",
    speech_act: SpeechAct = SpeechAct.PROPOSAL,
    artifacts: list[Artifact] | None = None,
    body: str = "",
) -> Utterance:
    return Utterance(
        thread_id=thread_id,
        speaker=AgentIdentity(name=speaker, constitution_version="1"),
        addressed_to="caucus",
        speech_act=speech_act,
        content=UtteranceContent(body=body, artifacts=artifacts or []),
    )


def _art(kind: str, **payload: Any) -> Artifact:
    return Artifact(kind=kind, payload=payload)


# ---------------------------------------------------------------------------
# Schema basics
# ---------------------------------------------------------------------------


class TestSeedBinding:
    def test_minimal_binding(self):
        sb = SeedBinding.model_validate({"from": "scoping", "kinds": ["adr"]})
        assert sb.from_meeting == "scoping"
        assert sb.kinds == ["adr"]
        assert sb.where == {}
        assert sb.limit is None
        assert sb.fallback is None

    def test_full_binding(self):
        sb = SeedBinding.model_validate(
            {
                "from": "contract-negotiation",
                "kinds": ["contract_note"],
                "where": {"state": "agreed"},
                "limit": 5,
                "fallback": "any",
            }
        )
        assert sb.where == {"state": "agreed"}
        assert sb.limit == 5
        assert sb.fallback == "any"

    def test_from_is_required(self):
        with pytest.raises(ValidationError):
            SeedBinding.model_validate({"kinds": ["adr"]})

    def test_kinds_is_required(self):
        with pytest.raises(ValidationError):
            SeedBinding.model_validate({"from": "scoping"})


class TestMeeting:
    def test_minimal_meeting(self):
        m = Meeting(id="x", label="Mx", goal="g", roster=["alice"])
        assert m.id == "x"
        assert m.convenor_directive == ""
        assert m.meeting_budget is None
        assert m.seeds == []

    def test_with_seeds(self):
        m = Meeting.model_validate(
            {
                "id": "decomposition",
                "label": "M2",
                "goal": "decompose",
                "roster": ["white_rabbit"],
                "convenor_directive": "Decompose the stories.",
                "meeting_budget": 0.30,
                "seeds": [{"from": "scoping", "kinds": ["story"]}],
            }
        )
        assert len(m.seeds) == 1
        assert m.seeds[0].from_meeting == "scoping"


class TestWorkflow:
    def test_minimal_workflow(self):
        wf = Workflow(name="t", description="d", meetings=[])
        assert wf.version == 1
        assert wf.defaults == WorkflowDefaults()

    def test_meeting_by_id(self):
        wf = Workflow(
            name="t",
            description="d",
            meetings=[
                Meeting(id="a", label="M1", goal="g", roster=["alice"]),
                Meeting(id="b", label="M2", goal="g", roster=["alice"]),
            ],
        )
        assert wf.meeting_by_id("a").label == "M1"
        assert wf.meeting_by_id("b").label == "M2"
        assert wf.meeting_by_id("missing") is None

    def test_entry_meeting_is_first(self):
        wf = Workflow(
            name="t",
            description="d",
            meetings=[
                Meeting(id="first", label="M1", goal="g", roster=["alice"]),
                Meeting(id="second", label="M2", goal="g", roster=["alice"]),
            ],
        )
        assert wf.entry_meeting.id == "first"

    def test_entry_meeting_raises_on_empty(self):
        wf = Workflow(name="t", description="d", meetings=[])
        with pytest.raises(ValueError, match="no meetings"):
            wf.entry_meeting


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class TestLoader:
    def test_loads_canonical_by_name(self):
        wf = load_workflow("canonical")
        assert wf.name == "canonical"
        assert len(wf.meetings) == 5
        assert [m.label for m in wf.meetings] == ["M1", "M2", "M3", "M4", "M5"]

    def test_loads_canonical_by_path(self):
        path = workflows_dir() / "canonical.yaml"
        wf = load_workflow(path)
        assert wf.name == "canonical"

    def test_loads_canonical_by_string_path(self):
        path = workflows_dir() / "canonical.yaml"
        wf = load_workflow(str(path))
        assert wf.name == "canonical"

    def test_missing_workflow_raises(self):
        with pytest.raises(FileNotFoundError, match="workflow not found"):
            load_workflow("does-not-exist")

    def test_missing_includes_available_list(self):
        with pytest.raises(FileNotFoundError, match="canonical"):
            load_workflow("does-not-exist")

    def test_list_workflows_includes_canonical(self):
        names = list_workflows()
        assert "canonical" in names


# ---------------------------------------------------------------------------
# Canonical workflow integrity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("workflow_name", list_workflows())
class TestBundledWorkflowIntegrity:
    """Integrity invariants every bundled workflow must satisfy.

    Parameterized over every YAML in closet/workflows/, so adding a
    new workflow file automatically adds new test runs. Catches the
    common mistakes (duplicate ids, dangling seed references,
    missing budgets, budget sum over cap) at unit-test time rather
    than at the cost of a live run.
    """

    @pytest.fixture
    def wf(self, workflow_name):
        return load_workflow(workflow_name)

    def test_meeting_ids_are_unique(self, wf):
        ids = [m.id for m in wf.meetings]
        assert len(ids) == len(set(ids)), f"duplicate meeting ids: {ids}"

    def test_meeting_labels_are_unique(self, wf):
        labels = [m.label for m in wf.meetings]
        assert len(labels) == len(set(labels))

    def test_seeds_reference_prior_meetings(self, wf):
        seen: set[str] = set()
        for meeting in wf.meetings:
            for seed in meeting.seeds:
                assert seed.from_meeting in seen or seed.from_meeting == "any", (
                    f"meeting {meeting.id!r} seeds from {seed.from_meeting!r} "
                    f"which is not a prior meeting (seen so far: {seen})"
                )
            seen.add(meeting.id)

    def test_entry_meeting_has_no_directive(self, wf):
        assert wf.entry_meeting.convenor_directive == ""

    def test_non_entry_meetings_have_directives(self, wf):
        for m in wf.meetings[1:]:
            assert m.convenor_directive.strip(), (
                f"meeting {m.id!r} has empty convenor_directive — only the "
                "entry meeting should be empty (it gets the user input)"
            )

    def test_every_meeting_has_a_budget(self, wf):
        for m in wf.meetings:
            assert m.meeting_budget is not None, (
                f"meeting {m.id!r} missing meeting_budget"
            )
            assert m.meeting_budget > 0

    def test_per_meeting_budget_sum_under_global_cap(self, wf):
        per_meeting_total = sum(m.meeting_budget or 0 for m in wf.meetings)
        global_cap = wf.defaults.budget_dollars or 0
        assert per_meeting_total <= global_cap, (
            f"per-meeting budgets sum to ${per_meeting_total:.2f} "
            f"but global cap is ${global_cap:.2f}"
        )

    def test_meetings_form_an_ordered_chain(self, wf):
        # Every non-entry meeting either seeds from at least one prior
        # meeting OR has no seeds (rare but valid — purely directive-driven).
        # The point is: no meeting accidentally references a meeting that
        # never appears in this workflow.
        all_ids = {m.id for m in wf.meetings}
        for meeting in wf.meetings:
            for seed in meeting.seeds:
                if seed.from_meeting != "any":
                    assert seed.from_meeting in all_ids, (
                        f"meeting {meeting.id!r} seeds from "
                        f"{seed.from_meeting!r} which doesn't exist in this "
                        f"workflow (members: {sorted(all_ids)})"
                    )


class TestCanonicalSpecifics:
    """Tests for the canonical workflow's particular shape — these
    invariants are about *the canonical 5-meeting sequence* and
    don't generalize to other workflows."""

    @pytest.fixture
    def wf(self):
        return load_workflow("canonical")

    def test_review_meeting_seeds_from_implementation(self, wf):
        review = wf.meeting_by_id("review")
        assert review is not None
        assert any(
            s.from_meeting == "implementation" and "implementation" in s.kinds
            for s in review.seeds
        ), "review should seed from implementation utterances"

    def test_implementation_meeting_filters_for_agreed_contracts(self, wf):
        impl = wf.meeting_by_id("implementation")
        assert impl is not None
        contract_seed = next(
            (
                s
                for s in impl.seeds
                if s.from_meeting == "contract-negotiation"
                and "contract_note" in s.kinds
            ),
            None,
        )
        assert contract_seed is not None
        assert contract_seed.where == {"state": "agreed"}
        assert contract_seed.fallback == "any"


class TestTDDSpecifics:
    """Tests for the TDD workflow's particular shape — what makes it
    different from canonical."""

    @pytest.fixture
    def wf(self):
        return load_workflow("tdd")

    def test_inserts_test_scenarios_meeting_between_contracts_and_impl(self, wf):
        ids = [m.id for m in wf.meetings]
        assert "test-scenarios" in ids
        assert ids.index("test-scenarios") == ids.index("contract-negotiation") + 1
        assert ids.index("implementation") == ids.index("test-scenarios") + 1

    def test_test_scenarios_meeting_includes_hatter(self, wf):
        ts = wf.meeting_by_id("test-scenarios")
        assert ts is not None
        assert "mad_hatter" in ts.roster

    def test_implementation_seeds_from_test_scenarios(self, wf):
        # The thing that makes this TDD: implementation reads Hatter's
        # tests as the closure criterion.
        impl = wf.meeting_by_id("implementation")
        assert impl is not None
        assert any(
            s.from_meeting == "test-scenarios" and "test_scenario" in s.kinds
            for s in impl.seeds
        ), "implementation should seed from test_scenarios"

    def test_has_more_meetings_than_canonical(self, wf):
        canonical = load_workflow("canonical")
        assert len(wf.meetings) > len(canonical.meetings), (
            "TDD workflow should add at least one meeting vs canonical"
        )


# ---------------------------------------------------------------------------
# YAML round-trip
# ---------------------------------------------------------------------------


class TestYAMLRoundTrip:
    def test_yaml_loads_as_workflow(self, tmp_path: Path):
        original = Workflow(
            name="round-trip",
            description="test",
            meetings=[
                Meeting(
                    id="m1",
                    label="M1",
                    goal="goal",
                    roster=["alice"],
                    meeting_budget=0.5,
                    seeds=[
                        SeedBinding.model_validate(
                            {"from": "any", "kinds": ["adr"], "limit": 1}
                        )
                    ],
                ),
            ],
        )
        path = tmp_path / "wf.yaml"
        path.write_text(yaml.safe_dump(original.model_dump(by_alias=True)))
        roundtripped = load_workflow(path)
        assert roundtripped.name == original.name
        assert roundtripped.meetings[0].seeds[0].from_meeting == "any"
        assert roundtripped.meetings[0].seeds[0].limit == 1


# ---------------------------------------------------------------------------
# WorkflowCapture
# ---------------------------------------------------------------------------


class TestWorkflowCapture:
    def test_only_keeps_artifact_carrying_utterances(self):
        cap = WorkflowCapture()
        cap.observe(_utt(thread_id="t", artifacts=[_art("adr", title="x")]))
        cap.observe(_utt(thread_id="t", artifacts=[]))  # no artifacts → dropped
        assert len(cap.utterances) == 1

    def test_utterances_for_meeting_filters_by_thread_id(self):
        cap = WorkflowCapture()
        cap.observe(_utt(thread_id="scoping", artifacts=[_art("adr")]))
        cap.observe(_utt(thread_id="decomposition", artifacts=[_art("ticket")]))
        cap.observe(_utt(thread_id="scoping", artifacts=[_art("story")]))
        scoping = cap.utterances_for("scoping")
        assert len(scoping) == 2
        assert all(u.thread_id == "scoping" for u in scoping)


# ---------------------------------------------------------------------------
# resolve_seeds
# ---------------------------------------------------------------------------


class TestResolveSeeds:
    @pytest.fixture
    def populated_capture(self) -> WorkflowCapture:
        cap = WorkflowCapture()
        cap.observe(_utt(thread_id="scoping", artifacts=[_art("story", title="s1")]))
        cap.observe(_utt(thread_id="scoping", artifacts=[_art("adr", title="a1")]))
        cap.observe(_utt(thread_id="decomposition", artifacts=[_art("ticket", title="t1")]))
        cap.observe(_utt(thread_id="decomposition", artifacts=[_art("ticket", title="t2")]))
        cap.observe(
            _utt(
                thread_id="contracts",
                artifacts=[_art("contract_note", title="c1", state="agreed")],
            )
        )
        cap.observe(
            _utt(
                thread_id="contracts",
                artifacts=[_art("contract_note", title="c2", state="proposed")],
            )
        )
        return cap

    def test_filters_by_kind(self, populated_capture):
        seeds = resolve_seeds(
            [SeedBinding.model_validate({"from": "scoping", "kinds": ["adr"]})],
            populated_capture,
        )
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].kind == "adr"

    def test_multiple_kinds_in_one_binding(self, populated_capture):
        seeds = resolve_seeds(
            [SeedBinding.model_validate({"from": "scoping", "kinds": ["adr", "story"]})],
            populated_capture,
        )
        assert len(seeds) == 2

    def test_limit_caps_results(self, populated_capture):
        seeds = resolve_seeds(
            [
                SeedBinding.model_validate(
                    {"from": "decomposition", "kinds": ["ticket"], "limit": 1}
                )
            ],
            populated_capture,
        )
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["title"] == "t1"

    def test_where_filter_matches_payload(self, populated_capture):
        seeds = resolve_seeds(
            [
                SeedBinding.model_validate(
                    {
                        "from": "contracts",
                        "kinds": ["contract_note"],
                        "where": {"state": "agreed"},
                    }
                )
            ],
            populated_capture,
        )
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["state"] == "agreed"

    def test_fallback_any_drops_where_when_empty(self, populated_capture):
        # No contracts in state=draft, but fallback: any should send all
        seeds = resolve_seeds(
            [
                SeedBinding.model_validate(
                    {
                        "from": "contracts",
                        "kinds": ["contract_note"],
                        "where": {"state": "draft"},
                        "fallback": "any",
                    }
                )
            ],
            populated_capture,
        )
        assert len(seeds) == 2  # both contracts despite the where filter

    def test_fallback_none_returns_empty_when_no_match(self, populated_capture):
        seeds = resolve_seeds(
            [
                SeedBinding.model_validate(
                    {
                        "from": "contracts",
                        "kinds": ["contract_note"],
                        "where": {"state": "draft"},
                    }
                )
            ],
            populated_capture,
        )
        assert seeds == []

    def test_from_any_pulls_across_meetings(self, populated_capture):
        seeds = resolve_seeds(
            [SeedBinding.model_validate({"from": "any", "kinds": ["story", "ticket"]})],
            populated_capture,
        )
        kinds = {a.kind for u in seeds for a in u.content.artifacts}
        assert kinds == {"story", "ticket"}

    def test_multiple_bindings_dedupe_by_id(self, populated_capture):
        # Same kind requested via two bindings — should appear once
        seeds = resolve_seeds(
            [
                SeedBinding.model_validate({"from": "scoping", "kinds": ["adr"]}),
                SeedBinding.model_validate({"from": "any", "kinds": ["adr"]}),
            ],
            populated_capture,
        )
        assert len(seeds) == 1


# ---------------------------------------------------------------------------
# run_workflow against a fake Runner
# ---------------------------------------------------------------------------


@dataclass
class FakeEvent:
    """Minimal stand-in for RunnerEvent."""

    kind: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class FakeTelemetry:
    call_count: int = 0


class FakeRunner:
    """Mimics the slice of Runner that run_workflow touches.

    Per-meeting scripts: a list of FakeEvent sequences keyed by thread_id.
    convene() picks the script for the current thread; events() yields
    them. Tracks calls/cost across meetings so the per-meeting deltas
    in MeetingEndEvent are exercised.
    """

    def __init__(self, scripts: dict[str, list[FakeEvent]]):
        self._scripts = scripts
        self._current_thread: str | None = None
        self.telemetry = FakeTelemetry()
        self.total_cost: float = 0.0
        self._completed = False
        # Track calls to convene for assertions
        self.convene_calls: list[dict[str, Any]] = []

    async def convene(
        self,
        *,
        thread_id: str,
        goal: str,
        roster: list[str],
        seed_utterances: list[Utterance],
        convenor_directive: str | None = None,
    ) -> None:
        self._current_thread = thread_id
        self.convene_calls.append(
            {
                "thread_id": thread_id,
                "goal": goal,
                "roster": list(roster),
                "seeds": list(seed_utterances),
                "convenor_directive": convenor_directive,
            }
        )

    async def events(self) -> AsyncIterator[FakeEvent]:
        # Cost/call accounting bumps as if the LLM ran.
        for ev in self._scripts.get(self._current_thread or "", []):
            if ev.kind == "utterance":
                self.telemetry.call_count += 1
                self.total_cost += 0.10
            yield ev
            await asyncio.sleep(0)


class TestRunWorkflow:
    @pytest.fixture
    def two_meeting_workflow(self) -> Workflow:
        return Workflow(
            name="t",
            description="d",
            meetings=[
                Meeting(
                    id="scoping",
                    label="M1",
                    goal="produce stories",
                    roster=["alice"],
                    meeting_budget=0.50,
                ),
                Meeting(
                    id="impl",
                    label="M2",
                    goal="ship",
                    roster=["tweedledum"],
                    convenor_directive="ship the code",
                    meeting_budget=1.00,
                    seeds=[
                        SeedBinding.model_validate(
                            {"from": "scoping", "kinds": ["story"]}
                        )
                    ],
                ),
            ],
        )

    async def test_emits_meeting_start_and_end_per_meeting(self, two_meeting_workflow):
        scripts = {
            "scoping": [
                FakeEvent(
                    "utterance",
                    {
                        "utterance": _utt(
                            thread_id="scoping",
                            speaker="alice",
                            artifacts=[_art("story", title="s1")],
                        )
                    },
                ),
                FakeEvent("complete"),
            ],
            "impl": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(two_meeting_workflow, runner, "user said do X"):
            events.append(ev)

        starts = [e for e in events if isinstance(e, MeetingStartEvent)]
        ends = [e for e in events if isinstance(e, MeetingEndEvent)]
        assert len(starts) == 2
        assert len(ends) == 2
        assert [s.meeting.id for s in starts] == ["scoping", "impl"]
        assert all(e.outcome == "COMPLETE" for e in ends)

    async def test_entry_meeting_gets_user_directive(self, two_meeting_workflow):
        scripts = {"scoping": [FakeEvent("complete")], "impl": [FakeEvent("complete")]}
        runner = FakeRunner(scripts)
        async for _ in run_workflow(two_meeting_workflow, runner, "USER DIRECTIVE"):
            pass
        assert runner.convene_calls[0]["convenor_directive"] == "USER DIRECTIVE"
        assert runner.convene_calls[1]["convenor_directive"] == "ship the code"

    async def test_seeds_pass_through_from_prior_meetings(self, two_meeting_workflow):
        story = _utt(
            thread_id="scoping",
            speaker="alice",
            artifacts=[_art("story", title="s1")],
        )
        scripts = {
            "scoping": [
                FakeEvent("utterance", {"utterance": story}),
                FakeEvent("complete"),
            ],
            "impl": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        async for _ in run_workflow(two_meeting_workflow, runner, "go"):
            pass
        impl_call = runner.convene_calls[1]
        assert len(impl_call["seeds"]) == 1
        assert impl_call["seeds"][0].id == story.id

    async def test_meeting_budget_caps_meeting_early(self):
        wf = Workflow(
            name="cap-test",
            description="d",
            meetings=[
                Meeting(
                    id="m",
                    label="M1",
                    goal="g",
                    roster=["alice"],
                    meeting_budget=0.15,
                ),
            ],
        )
        # Each utterance in our FakeRunner adds $0.10 — two should be enough
        # to exceed the $0.15 cap before we ever see the (never-emitted) complete.
        scripts = {
            "m": [
                FakeEvent("utterance", {"utterance": _utt(thread_id="m")}),
                FakeEvent("utterance", {"utterance": _utt(thread_id="m")}),
                FakeEvent("utterance", {"utterance": _utt(thread_id="m")}),
            ]
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(wf, runner, "go"):
            events.append(ev)
        end = next(e for e in events if isinstance(e, MeetingEndEvent))
        assert end.outcome == "MEETING_BUDGET"

    async def test_global_budget_aborts_workflow(self, two_meeting_workflow):
        scripts = {
            "scoping": [FakeEvent("budget_exceeded", {"cost": 99.0})],
            "impl": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(two_meeting_workflow, runner, "go"):
            events.append(ev)
        ends = [e for e in events if isinstance(e, MeetingEndEvent)]
        assert len(ends) == 1
        assert ends[0].outcome == "GLOBAL_BUDGET"
        # Second meeting should NOT have been convened
        assert len(runner.convene_calls) == 1

    async def test_meeting_end_reports_artifact_kinds(self, two_meeting_workflow):
        scripts = {
            "scoping": [
                FakeEvent(
                    "utterance",
                    {
                        "utterance": _utt(
                            thread_id="scoping",
                            artifacts=[_art("story"), _art("story"), _art("adr")],
                        )
                    },
                ),
                FakeEvent("complete"),
            ],
            "impl": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(two_meeting_workflow, runner, "go"):
            events.append(ev)
        scoping_end = next(
            e
            for e in events
            if isinstance(e, MeetingEndEvent) and e.meeting.id == "scoping"
        )
        assert scoping_end.artifact_kinds == {"story": 2, "adr": 1}

    async def test_canonical_workflow_can_be_driven_to_completion(self):
        # Ensures the bundled canonical workflow YAML is structurally
        # runnable end-to-end against a simple fake runner. Doesn't
        # assert about quality of artifacts (no real LLM here) — just
        # confirms the loader, seed resolver, and runner glue all
        # fit together for the load-bearing case.
        wf = load_workflow("canonical")
        scripts = {
            m.id: [
                FakeEvent(
                    "utterance",
                    {
                        "utterance": _utt(
                            thread_id=m.id,
                            artifacts=[_art("story"), _art("adr"), _art("ticket")],
                        )
                    },
                ),
                FakeEvent("complete"),
            ]
            for m in wf.meetings
        }
        runner = FakeRunner(scripts)
        starts = ends = 0
        async for ev in run_workflow(wf, runner, "user directive"):
            if isinstance(ev, MeetingStartEvent):
                starts += 1
            elif isinstance(ev, MeetingEndEvent):
                ends += 1
        assert starts == 5
        assert ends == 5
        assert len(runner.convene_calls) == 5
        # Entry meeting got the user directive
        assert runner.convene_calls[0]["convenor_directive"] == "user directive"
        # Subsequent meetings got their YAML directives
        for call, meeting in zip(runner.convene_calls[1:], wf.meetings[1:]):
            assert call["convenor_directive"] == meeting.convenor_directive
