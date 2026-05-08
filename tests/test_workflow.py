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


@pytest.mark.parametrize("workflow_name", ["canonical", "tdd"])
class TestDecompositionGroundingVoice:
    """Pins Alice's presence in M2 (decomposition) as the grounding
    voice. The literary parallel: in the book, every character's
    distinctive shape is legible because Alice is there to be confused
    by them — strip her out and the Cheshire Cat is just a slippery
    answerer rather than a slippery answerer to *Alice*. The framework
    operationalizes this in M2 by pairing Alice with Rabbit + Cat —
    she defends her stories when Rabbit's tickets compress them past
    user-recognition.
    """

    @pytest.fixture
    def m2(self, workflow_name):
        return load_workflow(workflow_name).meeting_by_id("decomposition")

    def test_alice_is_in_m2_roster(self, m2):
        assert m2 is not None
        assert "alice" in m2.roster, (
            "Alice belongs in M2 — Rabbit's anxious-thoroughness "
            "failure mode is decomposing past usefulness, and Alice's "
            "'would the persona actually care about this?' voice is "
            "the counter. See the literary-parallel discussion that "
            "filed this change."
        )

    def test_m2_directive_names_alice_as_grounding_voice(self, m2):
        assert m2 is not None
        directive = m2.convenor_directive.lower()
        assert "alice" in directive, (
            "M2 directive must explicitly call out Alice's role; she "
            "is in the room but defensive/observational by default — "
            "without the directive naming her job, the LLM doesn't "
            "know what move she should make."
        )
        assert "grounding voice" in directive or "user-facing point" in directive, (
            "M2 directive must name Alice's role as defensive (defending "
            "the user-facing point) rather than driving the decomposition. "
            "Without the framing, she'll either be silent (waste) or try to "
            "do Rabbit's job (muddy the meeting)."
        )


class TestCompositionPhase:
    """Pins the M2.5 feature-composition phase (TDD only). Per roadmap
    d1f4f2ec and analyses 026/027: M3 seeding from a single ticket
    forced Tweedles to generalize cross-stack coordination from one
    representative work unit, producing the inconsistent-frontend-vs-
    backend pattern. M2.5 groups tickets into features that span the
    stack coherently; M3 then negotiates seams against the feature.

    Caterpillar is here applying his "what does this claim?" stance
    one layer earlier than M6 — to the *promise* of the feature, not
    the shipped code. Alice extends her M2 grounding-voice role.
    Rabbit drives the grouping (he wrote the tickets).
    """

    @pytest.fixture
    def composition(self):
        return load_workflow("tdd").meeting_by_id("composition")

    def test_composition_meeting_exists_in_tdd(self, composition):
        assert composition is not None
        assert composition.label == "M2.5"
        assert composition.name == "Advice from a Caterpillar"

    def test_composition_meeting_does_not_exist_in_canonical(self):
        canonical = load_workflow("canonical")
        assert canonical.meeting_by_id("composition") is None, (
            "M2.5 ships in TDD first; canonical can follow if the "
            "experiment shows the phase earns its keep"
        )

    def test_composition_roster_has_rabbit_alice_caterpillar(self, composition):
        assert composition is not None
        assert set(composition.roster) == {"white_rabbit", "alice", "caterpillar"}, (
            "Rabbit drives (he wrote the tickets), Alice audits user-coherence "
            "(extending M2 role), Caterpillar audits feature-claim integrity "
            "(M6 stance applied earlier). Adding anyone else dilutes the focus."
        )

    def test_composition_directive_names_rabbits_feature_move(self, composition):
        assert composition is not None
        directive = composition.convenor_directive.lower()
        assert "feature" in directive
        assert "rabbit" in directive, (
            "Directive must name Rabbit's role explicitly; without it the "
            "LLM doesn't know which agent should drive the grouping"
        )

    def test_composition_directive_requires_persona_grounding(self, composition):
        assert composition is not None
        directive = composition.convenor_directive.lower()
        assert "persona" in directive, (
            "The persona requirement is the framework's anti-bag-of-tickets "
            "guard: if a feature can't name a persona it serves, it isn't a "
            "feature, it's a grouping convenience. Directive must surface this."
        )

    def test_composition_directive_names_stack_span(self, composition):
        assert composition is not None
        directive = composition.convenor_directive.lower()
        assert "stack_span" in directive or "stack-span" in directive or "stack span" in directive, (
            "stack_span is what M3 reads to decide whether contracts are "
            "one-sided or full-stack. Directive must name it so Rabbit "
            "produces it on every feature."
        )

    def test_composition_seeds_from_decomposition_tickets(self, composition):
        assert composition is not None
        ticket_seed = next(
            (s for s in composition.seeds if s.from_meeting == "decomposition"), None
        )
        assert ticket_seed is not None
        assert "ticket" in ticket_seed.kinds

    def test_tdd_m3_seeds_features_not_tickets(self):
        """The whole point of adding M2.5 — M3 negotiates contracts against
        features, not against a single representative ticket."""
        m3 = load_workflow("tdd").meeting_by_id("contract-negotiation")
        assert m3 is not None
        feature_seed = next(
            (s for s in m3.seeds if s.from_meeting == "composition"), None
        )
        assert feature_seed is not None, (
            "TDD M3 must seed from composition.feature so Tweedles get "
            "feature-bound contract scope. Otherwise M2.5 doesn't actually "
            "change downstream behavior."
        )
        assert "feature" in feature_seed.kinds
        ticket_seed = next(
            (s for s in m3.seeds if s.from_meeting == "decomposition"), None
        )
        assert ticket_seed is None, (
            "TDD M3 should no longer seed directly from decomposition.ticket "
            "— the composition phase aggregates them. Canonical M3 still does."
        )

    def test_canonical_m3_still_seeds_from_decomposition_ticket(self):
        """Canonical doesn't have M2.5, so its M3 still seeds tickets directly."""
        m3 = load_workflow("canonical").meeting_by_id("contract-negotiation")
        assert m3 is not None
        ticket_seed = next(
            (s for s in m3.seeds if s.from_meeting == "decomposition"), None
        )
        assert ticket_seed is not None
        assert "ticket" in ticket_seed.kinds

    def test_composition_directive_opens_with_rabbit_imperative(self, composition):
        """Per analysis 027 F1: Rabbit chose silence in M2.5 because the
        directive's structure (long preamble, role descriptions for all
        three agents, 'default to silence' framing) read as ambient
        rather than imperative. The fix is to lead with Rabbit's move
        explicitly. This test pins that Rabbit's imperative appears in
        the *first 200 characters* of the directive, before any role
        framing for Alice or Caterpillar.
        """
        assert composition is not None
        opening = composition.convenor_directive[:200].lower()
        assert "rabbit" in opening, (
            "Directive must open with Rabbit's role; without that the "
            "LLM reads the meeting as ambient and chooses silence"
        )

    def test_composition_directive_explicitly_rejects_silence_for_rabbit(
        self, composition
    ):
        """Same finding: Rabbit's default is silence-when-uncertain
        (correct in M2 where Alice and Cat are watching for grounding
        breaks), but M2.5 needs him to drive. The directive must name
        silence as wrong for Rabbit specifically.
        """
        assert composition is not None
        directive = composition.convenor_directive.lower()
        assert "silence is wrong" in directive, (
            "Without an explicit anti-silence statement, Rabbit's "
            "constitutional default-to-silence-when-uncertain wins and "
            "M2.5 produces no features (analysis 027 F1)"
        )

    def test_composition_directive_counters_chapter_title_bias(self, composition):
        """The meeting prefix '**M2.5 — Advice from a Caterpillar.**'
        primes the LLM toward 'this is Caterpillar's show.' The
        directive must explicitly name that the chapter title
        describes the *stance*, not the convenor — Rabbit drives.
        """
        assert composition is not None
        directive = composition.convenor_directive.lower()
        # Must reference the chapter title bias and counter it
        assert "chapter title" in directive or "caterpillar's chapter" in directive, (
            "Directive must explicitly counter the chapter-title bias "
            "introduced by the meeting name prefix"
        )


class TestTeaPartyScopesPerFeature:
    """Pins M4's per-feature scoping discipline added after analysis
    027. Without this, Hatter's open-ended 'what could break?' search
    produces test sprawl — analysis 027 saw 22 test files including
    several pairs of overlapping timezone/persistence scenarios. With
    features as the unit of scope and M6 named as the system-wide
    safety net, M4 is bounded and (hypothesized) cheaper.
    """

    @pytest.fixture
    def m4(self):
        return load_workflow("tdd").meeting_by_id("test-scenarios")

    def test_m4_seeds_features_from_composition(self, m4):
        """M4 needs features in its seed manifest; without them the
        per-feature scoping language has nothing to bind to and
        Hatter falls back to system-wide search.
        """
        assert m4 is not None
        feature_seed = next(
            (s for s in m4.seeds if s.from_meeting == "composition"), None
        )
        assert feature_seed is not None
        assert "feature" in feature_seed.kinds

    def test_m4_directive_scopes_tests_per_feature(self, m4):
        assert m4 is not None
        directive = m4.convenor_directive.lower()
        assert "scope" in directive and "per feature" in directive, (
            "M4 directive must explicitly bound test-writing to "
            "per-feature scope, otherwise Hatter generates system-wide "
            "edge tests and M4 sprawls (analysis 027)"
        )

    def test_m4_directive_names_m6_as_safety_net(self, m4):
        """The 'stop when feature is covered' discipline only works if
        the agents know there's a safety net for system-wide
        invariants. Naming M6 / Caterpillar's review explicitly as
        that safety net frees them from being exhaustive at this
        layer.
        """
        assert m4 is not None
        directive = m4.convenor_directive.lower()
        assert "m6" in directive or "caterpillar" in directive, (
            "M4 directive must point at M6/Caterpillar as the system-"
            "wide-invariants safety net so agents can stop at feature "
            "scope without anxiety about uncaught failure modes"
        )

    def test_m4_directive_bounds_hatter_lane(self, m4):
        """Per analysis 029 F5 + v7 follow-up: Hatter's §VIII failure
        mode (scenario sprawl + severity inflation) generalizes to
        BOTH meta-discussion sprawl AND out-of-lane code shipping.
        The directive must bound both — ship failure-mode scenarios
        and test files, raise ONE concern on process issues, no
        write_file calls into production code paths.

        Without these bounds, Hatter's character-shaped tendency to
        keep iterating on observations sprawls into:
          - team-process critique (properly Dodo's / Caterpillar's job)
          - direct production-code edits (properly the Tweedles' lane)

        v7 showed the meta-discussion bound shifted his content but
        he replaced it with src/backend/ write_file calls. Both
        need bounding.
        """
        assert m4 is not None
        directive = m4.convenor_directive.lower()
        assert "hatter" in directive
        assert "stay in your lane" in directive or "your lane" in directive, (
            "M4 directive must explicitly bound Hatter's role; without "
            "the lane-keeping language the LLM expands into meta-"
            "discussion (analysis 029 F5)"
        )
        # New (post-v7): must also forbid out-of-lane code shipping.
        assert "production code" in directive or "src/backend" in directive, (
            "M4 directive must forbid Hatter from shipping production "
            "code via write_file — v7 showed he shifted from meta-"
            "discussion sprawl to backend-code sprawl when only the "
            "first was bounded"
        )


class TestReviewBoundsScope:
    """Pins the M6 directive's scope-of-fix-work bound. Per analysis
    029, M6 went over budget across multiple runs because Tweedles
    accepted every Caterpillar finding — including refactor
    suggestions — as actionable. The directive must distinguish
    name-the-broken-bug findings (act on these) from speculative-
    improvement findings (push back as concern).
    """

    @pytest.fixture
    def m6(self):
        return load_workflow("tdd").meeting_by_id("review")

    def test_m6_directive_distinguishes_broken_from_refactor(self, m6):
        assert m6 is not None
        directive = m6.convenor_directive.lower()
        assert "refactor" in directive, (
            "M6 directive must name 'refactor' as the category Tweedles "
            "should NOT accept as actionable in M6 — only genuinely "
            "broken bugs warrant fix-during-review"
        )
        assert "broken" in directive or "bug" in directive


class TestFeatureSeedingFlowsThroughPipeline:
    """Pins that features Rabbit ships in M2.5 reach M3, M4, M5, and
    M6 through their seed queries. If a downstream meeting can't see
    features, the directive's references to features are factually
    wrong and the team will (correctly, per analysis 027) flag the
    mismatch as a concern.
    """

    @pytest.fixture
    def tdd(self):
        return load_workflow("tdd")

    def test_m3_sees_features(self, tdd):
        m3 = tdd.meeting_by_id("contract-negotiation")
        assert m3 is not None
        assert any(
            s.from_meeting == "composition" and "feature" in s.kinds
            for s in m3.seeds
        )

    def test_m4_sees_features(self, tdd):
        m4 = tdd.meeting_by_id("test-scenarios")
        assert m4 is not None
        assert any(
            s.from_meeting == "composition" and "feature" in s.kinds
            for s in m4.seeds
        )

    def test_m5_sees_features(self, tdd):
        m5 = tdd.meeting_by_id("implementation")
        assert m5 is not None
        assert any(
            s.from_meeting == "composition" and "feature" in s.kinds
            for s in m5.seeds
        )

    def test_m6_sees_features(self, tdd):
        m6 = tdd.meeting_by_id("review")
        assert m6 is not None
        assert any(
            s.from_meeting == "composition" and "feature" in s.kinds
            for s in m6.seeds
        )


@pytest.mark.parametrize(
    "workflow_name,impl_meeting_id",
    [("canonical", "implementation"), ("tdd", "implementation")],
)
class TestImplementationMeetingPathSafety:
    """Pins the implementation meeting's directive against the
    path-drift failure mode from analysis 024 — Tweedledee invented
    `src/frontend/` instead of using the skeleton's `frontend/src/`.

    The fix is content-only (clearer instructions in the directive),
    so the regression test is also content-only: assert the prompt
    contains the load-bearing phrasing. Avoids burning a live LLM
    run to validate a deterministic prompt change.
    """

    def test_directive_requires_list_files_before_write(
        self, workflow_name, impl_meeting_id
    ):
        wf = load_workflow(workflow_name)
        meeting = wf.meeting_by_id(impl_meeting_id)
        assert meeting is not None
        directive = meeting.convenor_directive.lower()
        assert "list_files" in directive, (
            f"{workflow_name}: implementation directive must mention list_files"
        )
        assert "before any" in directive or "first move" in directive, (
            f"{workflow_name}: implementation directive must order list_files "
            "BEFORE write_file (not just mention them as alternatives)"
        )

    def test_directive_forbids_inventing_top_level_directories(
        self, workflow_name, impl_meeting_id
    ):
        wf = load_workflow(workflow_name)
        meeting = wf.meeting_by_id(impl_meeting_id)
        assert meeting is not None
        directive = meeting.convenor_directive.lower()
        # The exact failure mode from analysis 024: Tweedledee invented
        # `src/frontend/` instead of using `frontend/src/`. Pin the fix.
        assert "do not invent" in directive or "do not create" in directive, (
            f"{workflow_name}: implementation directive must explicitly "
            "forbid inventing new top-level directories"
        )

    def test_directive_names_the_path_drift_example(
        self, workflow_name, impl_meeting_id
    ):
        wf = load_workflow(workflow_name)
        meeting = wf.meeting_by_id(impl_meeting_id)
        assert meeting is not None
        directive = meeting.convenor_directive
        # Naming the specific layout makes the instruction concrete.
        # Both `frontend/src/` and `src/backend/` are mentioned to
        # cover both Tweedles' domains.
        assert "frontend/src/" in directive, (
            f"{workflow_name}: implementation directive should name the "
            "skeleton's frontend layout to anchor Tweedledee"
        )
        assert "src/backend/" in directive, (
            f"{workflow_name}: implementation directive should name the "
            "skeleton's backend layout to anchor Tweedledum"
        )


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

    def test_test_scenarios_meeting_pairs_alice_and_hatter(self, wf):
        # The tea-party pairing — Alice for user-journey scenarios,
        # Hatter for failure-mode scenarios. Together they pin the
        # test pyramid M5's implementation has to satisfy.
        ts = wf.meeting_by_id("test-scenarios")
        assert ts is not None
        assert "mad_hatter" in ts.roster
        assert "alice" in ts.roster, (
            "Alice should be in M4 — without her, Tweedles backfill the "
            "user-journey test surface for their own implementation, "
            "which is the test-engineering anti-pattern Geocities v2 "
            "showed (1798 lines of contract tests written by the "
            "implementers rather than pinned by a test-engineering "
            "voice). See SHOWCASE / Geocities run."
        )

    def test_implementation_seeds_from_test_scenarios(self, wf):
        # The thing that makes this TDD: implementation reads M4's
        # tests as the closure criterion. After the tea-party pairing,
        # M5 pulls BOTH Hatter's test_scenarios and Alice's stories
        # (which she ships in M4 as user-journey form).
        impl = wf.meeting_by_id("implementation")
        assert impl is not None
        seed = next(
            (s for s in impl.seeds if s.from_meeting == "test-scenarios"),
            None,
        )
        assert seed is not None, "implementation should seed from test-scenarios"
        assert "test_scenario" in seed.kinds, (
            "implementation must pull Hatter's failure-mode scenarios"
        )
        assert "story" in seed.kinds, (
            "implementation must pull Alice's user-journey stories from M4 — "
            "the user-facing surface Hatter doesn't cover by character"
        )

    def test_has_more_meetings_than_canonical(self, wf):
        canonical = load_workflow("canonical")
        assert len(wf.meetings) > len(canonical.meetings), (
            "TDD workflow should add at least one meeting vs canonical"
        )

    def test_m4_directive_requires_both_artifact_and_write_file(self, wf):
        # Tea-party run exposed: Alice + Hatter shipped 24 markdown
        # scenarios but NEITHER called write_file to create runnable
        # .py test files. They treated "ship the scenario" as the
        # whole test step. Implementation in M5 cannot turn a markdown
        # artifact red→green; only a .py file. The directive must make
        # the two-operations-per-scenario requirement explicit, with
        # the failure mode named so the LLM doesn't skip step 2.
        ts = wf.meeting_by_id("test-scenarios")
        assert ts is not None
        directive = ts.convenor_directive
        # Must mention both operations
        assert "write_file" in directive
        # Must call out that artifact-without-test-file is the failure
        assert "documentation, not a test" in directive or "without a runnable test file" in directive, (
            "M4 directive must explicitly name the artifact-without-test-file "
            "failure mode (Alice + Hatter skip write_file because they treat "
            "shipping the scenario as the whole step). See tea-party run."
        )
        # Must explicitly name the directory the test files go to
        assert "tests/" in directive, (
            "M4 directive must name tests/ as the path the .py files go into"
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
        # Track calls to mark_thread_complete (workflow uses this to
        # close threads that exited via a non-COMPLETE outcome so the
        # late-publish guard can fire on slow deliberations).
        self.thread_completes: list[dict[str, str]] = []

    def mark_thread_complete(self, thread_id: str, reason: str) -> None:
        self.thread_completes.append({"thread_id": thread_id, "reason": reason})

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

    async def events(
        self, *, terminal_thread_id: str | None = None
    ) -> AsyncIterator[FakeEvent]:
        # Cost/call accounting bumps as if the LLM ran.
        # Mirrors the real Runner.events() filter: stale `complete`
        # events from other threads should be yielded but not end
        # iteration when terminal_thread_id is set.
        for ev in self._scripts.get(self._current_thread or "", []):
            if ev.kind == "utterance":
                self.telemetry.call_count += 1
                self.total_cost += 0.10
            yield ev
            await asyncio.sleep(0)
            if ev.kind in ("aborted", "timeout"):
                return
            if ev.kind == "complete":
                if terminal_thread_id is None:
                    return
                event_thread_id = (ev.payload or {}).get("thread_id")
                if event_thread_id is None or event_thread_id == terminal_thread_id:
                    return


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

    async def test_directive_body_is_prefixed_with_meeting_name(self):
        """The literary parallel is load-bearing only if agents see the
        name. run_workflow prefixes the convenor directive with the
        meeting's label + name before passing it to convene(), so the
        Dodo-relayed directive utterance carries the framing into the
        agents' context.
        """
        wf = Workflow(
            name="named",
            description="d",
            meetings=[
                Meeting(
                    id="m1",
                    label="M1",
                    name="The Caucus Race",
                    goal="g",
                    roster=["alice"],
                    meeting_budget=0.50,
                ),
                Meeting(
                    id="m2",
                    label="M2",
                    goal="g",
                    roster=["alice"],
                    convenor_directive="do the thing",
                    meeting_budget=0.50,
                ),
            ],
        )
        scripts = {
            "m1": [FakeEvent("complete")],
            "m2": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        async for _ in run_workflow(wf, runner, "user input directive"):
            pass

        # M1 is the entry meeting — body is the user's directive plus the
        # name prefix.
        m1_call = runner.convene_calls[0]
        assert m1_call["convenor_directive"].startswith(
            "**M1 — The Caucus Race.**"
        )
        assert "user input directive" in m1_call["convenor_directive"]

        # M2 has no name — should still get the label prefix for orientation,
        # without name boilerplate.
        m2_call = runner.convene_calls[1]
        assert m2_call["convenor_directive"].startswith("**M2.**")
        assert "Caucus Race" not in m2_call["convenor_directive"]
        assert "do the thing" in m2_call["convenor_directive"]

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
        # Body is the user directive plus the meeting label/name prefix
        # the workflow injects (so agents see the meeting framing).
        assert "USER DIRECTIVE" in runner.convene_calls[0]["convenor_directive"]
        assert runner.convene_calls[0]["convenor_directive"].startswith("**M1.**")
        assert "ship the code" in runner.convene_calls[1]["convenor_directive"]
        assert runner.convene_calls[1]["convenor_directive"].startswith("**M2.**")

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

    async def test_meeting_budget_marks_thread_complete(self):
        """When MEETING_BUDGET caps a meeting, run_workflow must mark
        the thread COMPLETE so the late-publish guard suppresses any
        in-flight deliberation that lands after the cap fires.

        Regression test for the M5 race documented in analysis 026: an
        agent's slow LLM call landed test_scenarios on a still-RUNNING
        (but abandoned) thread, the workflow capture miscounted them
        against the wrong meeting, and the next meeting's seed query
        missed them entirely.
        """
        wf = Workflow(
            name="cap-marks-complete",
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
        scripts = {
            "m": [
                FakeEvent("utterance", {"utterance": _utt(thread_id="m")}),
                FakeEvent("utterance", {"utterance": _utt(thread_id="m")}),
            ]
        }
        runner = FakeRunner(scripts)
        async for _ in run_workflow(wf, runner, "go"):
            pass
        assert len(runner.thread_completes) == 1, (
            "MEETING_BUDGET exit must trigger exactly one mark_thread_complete "
            "so the runner's late-publish guard can suppress slow deliberations"
        )
        call = runner.thread_completes[0]
        assert call["thread_id"] == "m"
        assert "MEETING_BUDGET" in call["reason"]

    async def test_leaked_complete_event_from_prior_meeting_does_not_end_next(self):
        """Regression test for the cross-meeting event leakage pattern.

        Documented in the pomodoro test run: when a meeting exited via
        MEETING_BUDGET, mark_thread_complete generated a `complete`
        runner event with the prior meeting's thread_id. That event
        sat in the runner's queue. When the next meeting's events loop
        started consuming, it saw `kind="complete"` and exited
        immediately — even though the event was for a different
        thread. Result: the next meeting ended in 0 calls / 0s with no
        agent deliberation, observed across analyses 026 and 027 and
        identified definitively in the pomodoro run.

        The fix filters `complete` events by thread_id. This test
        emits a complete event with a *different* thread_id during a
        meeting and asserts the meeting does not exit on it.
        """
        wf = Workflow(
            name="leak",
            description="d",
            meetings=[
                Meeting(
                    id="real",
                    label="M1",
                    goal="g",
                    roster=["alice"],
                    meeting_budget=1.00,
                ),
            ],
        )
        scripts = {
            "real": [
                # First event: a leaked `complete` from a prior thread.
                # Without the fix, this ends the meeting immediately.
                FakeEvent("complete", {"thread_id": "previous-meeting"}),
                # Then a real utterance happens on the actual meeting.
                FakeEvent("utterance", {"utterance": _utt(thread_id="real")}),
                # And finally the meeting's own complete event.
                FakeEvent("complete", {"thread_id": "real"}),
            ],
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(wf, runner, "go"):
            events.append(ev)
        end = next(e for e in events if isinstance(e, MeetingEndEvent))
        assert end.outcome == "COMPLETE"
        # The meeting must have actually run — at least one utterance
        # observed and at least one LLM call billed (the FakeRunner
        # bumps call_count on each utterance event).
        assert end.calls_delta >= 1, (
            "Leaked complete event from prior meeting must not short-"
            "circuit the current meeting's events loop"
        )

    async def test_complete_meeting_does_not_force_thread_complete(self):
        """Complementary pin: a meeting that exits via the natural
        'complete' event already had its thread transitioned by the
        ThreadMonitor's normal completion path. run_workflow must NOT
        re-trigger the transition — that would emit a duplicate state
        change and confuse downstream subscribers.
        """
        wf = Workflow(
            name="complete-clean",
            description="d",
            meetings=[
                Meeting(
                    id="m",
                    label="M1",
                    goal="g",
                    roster=["alice"],
                    meeting_budget=1.00,
                ),
            ],
        )
        scripts = {"m": [FakeEvent("complete")]}
        runner = FakeRunner(scripts)
        async for _ in run_workflow(wf, runner, "go"):
            pass
        assert runner.thread_completes == [], (
            "natural COMPLETE must not trigger mark_thread_complete; "
            "the monitor already transitioned via the convenor's acknowledgment"
        )

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
        # Entry meeting got the user directive (with meeting label/name
        # prefix injected by run_workflow so agents see the framing).
        assert "user directive" in runner.convene_calls[0]["convenor_directive"]
        # Subsequent meetings got their YAML directive bodies, also
        # prefixed with their label/name.
        for call, meeting in zip(runner.convene_calls[1:], wf.meetings[1:]):
            assert meeting.convenor_directive in call["convenor_directive"]
            assert call["convenor_directive"].startswith(f"**{meeting.label}")


# ---------------------------------------------------------------------------
# per_item — schema, seed slicing, iteration logic
# ---------------------------------------------------------------------------


class TestPerItemSchema:
    def test_meeting_accepts_per_item(self):
        m = Meeting(
            id="test-scenarios",
            label="M4",
            goal="g",
            roster=["alice"],
            per_item="feature",
        )
        assert m.per_item == "feature"

    def test_meeting_per_item_defaults_to_none(self):
        m = Meeting(id="m", label="M1", goal="g", roster=["alice"])
        assert m.per_item is None


class TestPerItemSeedResolution:
    """resolve_seeds gains iteration awareness when per_item is in play.

    The two slicing rules under test:
      1) seed bindings whose kinds include the iteration kind get sliced
         to artifacts whose payload.slug matches the current item;
      2) seed bindings whose ``from`` references another per_item
         meeting get sliced to the iteration thread that pairs with
         the current item.
    """

    def _capture_with_features(self, slugs: list[str]) -> WorkflowCapture:
        """Build a capture containing one composition utterance per
        feature slug, each carrying a single feature artifact."""
        cap = WorkflowCapture()
        for slug in slugs:
            cap.observe(
                _utt(
                    thread_id="composition",
                    artifacts=[_art("feature", slug=slug, title=slug.title())],
                )
            )
        return cap

    def test_iteration_kind_filter_slices_to_current_slug(self):
        cap = self._capture_with_features(["sessions", "breaks", "history"])
        # M4 iteration for "breaks" — seed binding pulls features.
        out = resolve_seeds(
            [SeedBinding(**{"from": "composition", "kinds": ["feature"]})],
            cap,
            per_item_meetings={"test-scenarios": "feature", "implementation": "feature"},
            current_item_kind="feature",
            current_item_slug="breaks",
        )
        assert len(out) == 1
        feature_arts = [a for a in out[0].content.artifacts if a.kind == "feature"]
        assert feature_arts[0].payload["slug"] == "breaks"

    def test_no_slicing_when_not_in_iteration(self):
        # Same capture, but resolved without iteration context — caller
        # is a non-per_item meeting like M3 contract negotiation. All
        # features come through.
        cap = self._capture_with_features(["sessions", "breaks", "history"])
        out = resolve_seeds(
            [SeedBinding(**{"from": "composition", "kinds": ["feature"]})],
            cap,
        )
        assert len(out) == 3

    def test_paired_iteration_thread_filter(self):
        """M5 iteration for feature N pulls from M4 iteration N's
        thread, not from M4 iterations for other features."""
        cap = WorkflowCapture()
        # Three M4 iterations, each emitting test_scenario artifacts
        # under their feature-scoped thread_id.
        for slug in ("sessions", "breaks", "history"):
            cap.observe(
                _utt(
                    thread_id=f"test-scenarios-{slug}",
                    artifacts=[_art("test_scenario", title=f"{slug}-scenario")],
                )
            )

        out = resolve_seeds(
            [
                SeedBinding(
                    **{"from": "test-scenarios", "kinds": ["test_scenario"]}
                )
            ],
            cap,
            per_item_meetings={"test-scenarios": "feature", "implementation": "feature"},
            current_item_kind="feature",
            current_item_slug="breaks",
        )
        # Only the breaks-iteration thread contributes
        assert len(out) == 1
        assert out[0].thread_id == "test-scenarios-breaks"

    def test_per_item_source_without_paired_iteration_falls_through(self):
        """If the source meeting was per_item but the paired iteration
        thread produced no matching artifacts, fall through to the
        union of all iteration threads. This is the ``no scenarios for
        this feature yet`` case — better to seed with adjacent context
        than nothing."""
        cap = WorkflowCapture()
        cap.observe(
            _utt(
                thread_id="test-scenarios-sessions",
                artifacts=[_art("test_scenario", title="sessions-scenario")],
            )
        )
        # No artifacts under test-scenarios-breaks
        out = resolve_seeds(
            [
                SeedBinding(
                    **{"from": "test-scenarios", "kinds": ["test_scenario"]}
                )
            ],
            cap,
            per_item_meetings={"test-scenarios": "feature", "implementation": "feature"},
            current_item_kind="feature",
            current_item_slug="breaks",
        )
        assert len(out) == 1
        assert out[0].thread_id == "test-scenarios-sessions"


class TestPerItemIteration:
    """run_workflow loops a per_item meeting once per matching artifact."""

    @pytest.fixture
    def per_item_workflow(self) -> Workflow:
        # Two-meeting workflow: composition emits features, then
        # test-scenarios runs per_item on them.
        return Workflow(
            name="per-item-test",
            description="d",
            meetings=[
                Meeting(
                    id="composition",
                    label="M2.5",
                    goal="ship features",
                    roster=["alice"],
                    meeting_budget=1.0,
                ),
                Meeting(
                    id="test-scenarios",
                    label="M4",
                    goal="scenarios per feature",
                    roster=["alice", "mad_hatter"],
                    meeting_budget=0.5,
                    per_item="feature",
                    seeds=[
                        SeedBinding(**{"from": "composition", "kinds": ["feature"]})
                    ],
                ),
            ],
        )

    async def test_iterates_once_per_feature(self, per_item_workflow):
        # composition emits 3 features; test-scenarios runs 3 times.
        scripts = {
            "composition": [
                FakeEvent(
                    "utterance",
                    {
                        "utterance": _utt(
                            thread_id="composition",
                            artifacts=[
                                _art("feature", slug="sessions", title="Sessions"),
                                _art("feature", slug="breaks", title="Breaks"),
                                _art("feature", slug="history", title="History"),
                            ],
                        )
                    },
                ),
                FakeEvent("complete"),
            ],
            "test-scenarios-sessions": [FakeEvent("complete", {"thread_id": "test-scenarios-sessions"})],
            "test-scenarios-breaks": [FakeEvent("complete", {"thread_id": "test-scenarios-breaks"})],
            "test-scenarios-history": [FakeEvent("complete", {"thread_id": "test-scenarios-history"})],
        }
        runner = FakeRunner(scripts)
        starts: list[MeetingStartEvent] = []
        ends: list[MeetingEndEvent] = []
        async for ev in run_workflow(per_item_workflow, runner, "go"):
            if isinstance(ev, MeetingStartEvent):
                starts.append(ev)
            elif isinstance(ev, MeetingEndEvent):
                ends.append(ev)

        # 1 (composition) + 3 (test-scenarios iterations) = 4
        assert len(starts) == 4
        assert len(ends) == 4
        # All four convene calls happened
        thread_ids = [c["thread_id"] for c in runner.convene_calls]
        assert thread_ids == [
            "composition",
            "test-scenarios-sessions",
            "test-scenarios-breaks",
            "test-scenarios-history",
        ]
        # Iteration metadata present on the M4 events
        m4_starts = [s for s in starts if s.meeting.id == "test-scenarios"]
        assert len(m4_starts) == 3
        for idx, s in enumerate(m4_starts):
            assert s.iteration_index == idx + 1
            assert s.iteration_total == 3
            assert s.thread_id == f"test-scenarios-{['sessions', 'breaks', 'history'][idx]}"
            assert s.iteration_label in ("Sessions", "Breaks", "History")

    async def test_each_iteration_seeded_with_only_its_feature(
        self, per_item_workflow
    ):
        # Verify the slicing rule from TestPerItemSeedResolution at the
        # run_workflow level: each iteration's convene_call seeds list
        # contains exactly one feature artifact, and it's the one
        # matching the current iteration's slug.
        scripts = {
            "composition": [
                FakeEvent(
                    "utterance",
                    {
                        "utterance": _utt(
                            thread_id="composition",
                            artifacts=[
                                _art("feature", slug=s, title=s.title())
                                for s in ("sessions", "breaks", "history")
                            ],
                        )
                    },
                ),
                FakeEvent("complete"),
            ],
            "test-scenarios-sessions": [
                FakeEvent("complete", {"thread_id": "test-scenarios-sessions"})
            ],
            "test-scenarios-breaks": [
                FakeEvent("complete", {"thread_id": "test-scenarios-breaks"})
            ],
            "test-scenarios-history": [
                FakeEvent("complete", {"thread_id": "test-scenarios-history"})
            ],
        }
        runner = FakeRunner(scripts)
        async for _ in run_workflow(per_item_workflow, runner, "go"):
            pass
        # Skip composition; check the three iteration calls
        for call in runner.convene_calls[1:]:
            seeds = call["seeds"]
            # Each iteration should see exactly one utterance whose
            # feature artifact matches the iteration's slug.
            slug_in_thread = call["thread_id"].removeprefix("test-scenarios-")
            assert len(seeds) == 1
            feature_arts = [a for a in seeds[0].content.artifacts if a.kind == "feature"]
            assert len(feature_arts) == 1
            assert feature_arts[0].payload["slug"] == slug_in_thread

    async def test_per_item_with_no_matching_items_emits_synthetic_skip(self):
        # If a per_item meeting runs but no matching artifacts were
        # ever captured, emit a synthetic MeetingStart/End so the
        # consumer sees the meeting was acknowledged (fail-loud).
        wf = Workflow(
            name="no-features",
            description="d",
            meetings=[
                Meeting(
                    id="composition",
                    label="M2.5",
                    goal="g",
                    roster=["alice"],
                    meeting_budget=1.0,
                ),
                Meeting(
                    id="test-scenarios",
                    label="M4",
                    goal="g",
                    roster=["alice"],
                    per_item="feature",
                ),
            ],
        )
        scripts = {
            # composition ships nothing of kind=feature
            "composition": [FakeEvent("complete")],
        }
        runner = FakeRunner(scripts)
        events = []
        async for ev in run_workflow(wf, runner, "go"):
            events.append(ev)
        m4_starts = [
            e
            for e in events
            if isinstance(e, MeetingStartEvent) and e.meeting.id == "test-scenarios"
        ]
        m4_ends = [
            e
            for e in events
            if isinstance(e, MeetingEndEvent) and e.meeting.id == "test-scenarios"
        ]
        assert len(m4_starts) == 1
        assert len(m4_ends) == 1
        assert m4_starts[0].iteration_label == "(no items)"
        assert m4_ends[0].outcome == "COMPLETE"
        # Critically: no convene was issued for an empty iteration set
        thread_ids = [c["thread_id"] for c in runner.convene_calls]
        assert "test-scenarios" not in thread_ids
        assert all(not t.startswith("test-scenarios-") for t in thread_ids)


class TestTddSerialWorkflow:
    """The bundled tdd-serial.yaml is structurally runnable."""

    def test_loads(self):
        wf = load_workflow("tdd-serial")
        assert wf.name == "tdd-serial"
        per_item_meetings = [m for m in wf.meetings if m.per_item is not None]
        # M4 and M5 both per_item: feature
        assert {m.id for m in per_item_meetings} == {
            "test-scenarios",
            "implementation",
        }
        assert all(m.per_item == "feature" for m in per_item_meetings)

    async def test_can_be_driven_to_completion(self):
        # Drive the full tdd-serial workflow against a fake runner.
        # composition emits two features; M4/M5 each iterate twice;
        # other meetings run once. Verifies the YAML + run_workflow
        # + per_item iteration glue all fit.
        wf = load_workflow("tdd-serial")
        feature_slugs = ["sessions", "breaks"]

        def _ship_features(thread_id):
            return _utt(
                thread_id=thread_id,
                artifacts=[
                    _art("feature", slug=s, title=s.title()) for s in feature_slugs
                ],
            )

        scripts: dict[str, list[FakeEvent]] = {}
        for m in wf.meetings:
            if m.per_item is None:
                # Plain meeting ships representative artifacts based
                # on what its directive expects to produce.
                if m.id == "composition":
                    arts = {"utterance": _ship_features("composition")}
                else:
                    arts = {
                        "utterance": _utt(
                            thread_id=m.id,
                            artifacts=[
                                _art("story"),
                                _art("ticket"),
                                _art("contract_note", state="agreed"),
                                _art("implementation"),
                            ],
                        )
                    }
                scripts[m.id] = [FakeEvent("utterance", arts), FakeEvent("complete")]
            else:
                # per_item meeting — script each iteration thread_id
                # to ship a feature-relevant artifact + complete.
                for slug in feature_slugs:
                    iter_tid = f"{m.id}-{slug}"
                    scripts[iter_tid] = [
                        FakeEvent(
                            "utterance",
                            {
                                "utterance": _utt(
                                    thread_id=iter_tid,
                                    artifacts=[
                                        _art("test_scenario" if m.id == "test-scenarios" else "implementation"),
                                    ],
                                )
                            },
                        ),
                        FakeEvent("complete", {"thread_id": iter_tid}),
                    ]

        runner = FakeRunner(scripts)
        starts: list[MeetingStartEvent] = []
        ends: list[MeetingEndEvent] = []
        async for ev in run_workflow(wf, runner, "directive"):
            if isinstance(ev, MeetingStartEvent):
                starts.append(ev)
            elif isinstance(ev, MeetingEndEvent):
                ends.append(ev)

        # 5 plain meetings (M1, M2, M2.5, M3, M6) + 2 M4 iterations
        # + 2 M5 iterations = 9 starts + 9 ends.
        assert len(starts) == 9
        assert len(ends) == 9
        # All ends are COMPLETE
        assert all(e.outcome == "COMPLETE" for e in ends), (
            [e.outcome for e in ends]
        )
        # Iteration thread_ids are the expected per-feature pattern
        m4_threads = [
            s.thread_id for s in starts if s.meeting.id == "test-scenarios"
        ]
        m5_threads = [
            s.thread_id for s in starts if s.meeting.id == "implementation"
        ]
        assert m4_threads == ["test-scenarios-sessions", "test-scenarios-breaks"]
        assert m5_threads == ["implementation-sessions", "implementation-breaks"]
