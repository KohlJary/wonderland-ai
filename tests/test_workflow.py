"""Tests for wonderland.workflow — schema validation + loader.

Covers the data-on-disk workflow substrate. Execution (Workflow.run)
lands in its own module + tests once the runner integration is in.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from wonderland.workflow import (
    Meeting,
    SeedBinding,
    Workflow,
    WorkflowDefaults,
    list_workflows,
    load_workflow,
    workflows_dir,
)


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


class TestCanonical:
    @pytest.fixture
    def wf(self):
        return load_workflow("canonical")

    def test_meeting_ids_are_unique(self, wf):
        ids = [m.id for m in wf.meetings]
        assert len(ids) == len(set(ids)), f"duplicate meeting ids: {ids}"

    def test_meeting_labels_are_unique(self, wf):
        labels = [m.label for m in wf.meetings]
        assert len(labels) == len(set(labels))

    def test_seeds_reference_prior_meetings(self, wf):
        # Every seed binding must reference a meeting that appears
        # earlier in the sequence (or "any").
        seen: set[str] = set()
        for meeting in wf.meetings:
            for seed in meeting.seeds:
                assert seed.from_meeting in seen or seed.from_meeting == "any", (
                    f"meeting {meeting.id!r} seeds from {seed.from_meeting!r} "
                    f"which is not a prior meeting (seen so far: {seen})"
                )
            seen.add(meeting.id)

    def test_entry_meeting_has_no_directive(self, wf):
        # The entry meeting receives the user's runtime directive, so
        # the YAML should leave convenor_directive empty.
        assert wf.entry_meeting.convenor_directive == ""

    def test_non_entry_meetings_have_directives(self, wf):
        for m in wf.meetings[1:]:
            assert m.convenor_directive.strip(), (
                f"meeting {m.id!r} has empty convenor_directive — only the "
                "entry meeting should be empty (it gets the user input)"
            )

    def test_every_meeting_has_a_budget(self, wf):
        # Per-meeting budgets matter — without them one meeting can starve
        # the rest of the global cap.
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
            f"but global cap is ${global_cap:.2f} — meetings could starve each other"
        )

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


# ---------------------------------------------------------------------------
# YAML round-trip — sanity that the format is what it claims
# ---------------------------------------------------------------------------


class TestYAMLRoundTrip:
    def test_yaml_loads_as_workflow(self, tmp_path: Path):
        # Synthesize a minimal valid workflow, dump, reload, verify.
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
