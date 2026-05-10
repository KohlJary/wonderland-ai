"""Tests for cross-run seed continuity via disk-backed artifact
fallback (analysis 039 redux fix)."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.seeds_fallback import (
    disk_seeds_for_kinds,
    supported_disk_kinds,
)
from wonderland.utterance import SpeechAct


# --- Empty-state behavior ---


def test_disk_seeds_empty_when_project_has_no_wonderland_dir(
    tmp_path: Path,
) -> None:
    """Project that's never been run on returns no seeds."""
    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket", "story"], thread_id="composition"
    )
    assert seeds == []


def test_disk_seeds_empty_for_unsupported_kind(tmp_path: Path) -> None:
    """A kind we don't have a loader for is silently skipped."""
    seeds = disk_seeds_for_kinds(
        tmp_path, ["nonexistent-kind"], thread_id="x"
    )
    assert seeds == []


def test_disk_seeds_empty_when_registry_dir_exists_but_empty(
    tmp_path: Path,
) -> None:
    """Empty registry directories are not an error."""
    (tmp_path / ".wonderland" / "tickets").mkdir(parents=True)
    seeds = disk_seeds_for_kinds(tmp_path, ["ticket"], thread_id="x")
    assert seeds == []


# --- Loaded-state behavior ---


def test_disk_seeds_loads_tickets_from_disk(tmp_path: Path) -> None:
    """When tickets exist on disk, they surface as synthetic
    utterances with the right speech_act + speaker."""
    from wonderland.ticket import TicketPayload, TicketRegistry

    registry = TicketRegistry(tmp_path)
    registry.write(TicketPayload(
        title="Build account aggregation API",
        owner="tweedledum",
        tier="v1",
        estimate="2 days",
        description="Aggregate account balances for Maya's dashboard.",
        sources=["see-my-money-at-a-glance"],
    ))
    registry.write(TicketPayload(
        title="Build transaction list UI",
        owner="tweedledee",
        tier="v1",
        estimate="1 day",
        description="List recent transactions in a TUI table.",
        sources=["see-my-money-at-a-glance"],
    ))

    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket"], thread_id="decomposition"
    )
    assert len(seeds) == 2
    # Speaker matches the agent who normally produces tickets.
    for seed in seeds:
        assert seed.speaker.name == "white_rabbit"
        assert seed.speech_act == SpeechAct.TICKET
        assert seed.is_seed is True
        assert seed.thread_id == "decomposition"
        assert len(seed.content.artifacts) == 1
        assert seed.content.artifacts[0].kind == "ticket"
    # Records came through with title.
    titles = {s.content.artifacts[0].payload["title"] for s in seeds}
    assert "Build account aggregation API" in titles
    assert "Build transaction list UI" in titles


def test_disk_seeds_loads_stories(tmp_path: Path) -> None:
    """Stories synthesize with alice as speaker."""
    from wonderland.story import StoryPayload, StoryRegistry

    StoryRegistry(tmp_path).write(StoryPayload(
        title="See my money at a glance",
        persona="Maya, freelance translator",
        situation="Sunday evening, five tabs open.",
        need="Glance and know.",
        acceptance=["Single view", "All accounts visible"],
        tier="core",
        confusion_flags=["What counts as 'recent' for transactions?"],
    ))
    seeds = disk_seeds_for_kinds(tmp_path, ["story"], thread_id="scoping")
    assert len(seeds) == 1
    assert seeds[0].speaker.name == "alice"
    assert seeds[0].speech_act == SpeechAct.STORY


def test_disk_seeds_multiple_kinds_in_one_call(tmp_path: Path) -> None:
    """A single call with multiple kinds returns synthesized utterances
    for each kind that has files."""
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.story import StoryPayload, StoryRegistry

    TicketRegistry(tmp_path).write(TicketPayload(
        title="T",
        owner="tweedledum",
        tier="v1",
        estimate="1 day",
        description="d",
        sources=["x"],
    ))
    StoryRegistry(tmp_path).write(StoryPayload(
        title="S",
        persona="P",
        situation="x",
        need="y",
        acceptance=["a"],
        tier="core",
        confusion_flags=["unsure"],
    ))

    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket", "story"], thread_id="composition"
    )
    assert len(seeds) == 2
    kinds = {s.content.artifacts[0].kind for s in seeds}
    assert kinds == {"ticket", "story"}


def test_disk_seeds_artifact_payload_has_slug_for_per_item_slicing(
    tmp_path: Path,
) -> None:
    """The synthesized artifact's payload carries `slug` so the
    resolve_seeds per-item slicing logic can route the right feature
    to the right iteration."""
    from wonderland.feature import FeaturePayload, FeatureRegistry

    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Balance dashboard",
        description="Show account balances at a glance.",
        tickets=["build-balance-card-ui"],
        stack_span="full-stack",
        tier="v1",
        sources=["see-my-money-at-a-glance"],
    ))
    seeds = disk_seeds_for_kinds(
        tmp_path, ["feature"], thread_id="composition"
    )
    assert len(seeds) == 1
    payload = seeds[0].content.artifacts[0].payload
    assert payload["slug"] == "balance-dashboard"
    assert payload["number"] == 1
    assert payload["title"] == "Balance dashboard"
    assert "path" in payload


# --- supported_disk_kinds ---


def test_supported_disk_kinds_includes_load_bearing_artifacts() -> None:
    """The kinds that matter most for cross-run continuity are wired."""
    kinds = supported_disk_kinds()
    assert "ticket" in kinds
    assert "story" in kinds
    assert "feature" in kinds
    assert "adr" in kinds
    assert "contract_note" in kinds


# --- Integration with resolve_seeds ---


class TestResolveSeedsDiskFallback:
    """resolve_seeds wires disk fallback when project_root is set
    AND the bus query for a binding produces no results. Bus content
    always wins when present."""

    def _empty_capture(self):
        from wonderland.workflow import WorkflowCapture

        return WorkflowCapture()

    def test_bus_results_skip_disk_fallback(self, tmp_path: Path) -> None:
        """If the bus has matching utterances, disk content does NOT
        get added (bus is authoritative)."""
        from wonderland.story import StoryPayload, StoryRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.utterance import (
            AgentIdentity,
            Artifact,
            Utterance,
            UtteranceContent,
        )
        from wonderland.workflow import (
            SeedBinding,
            WorkflowCapture,
            resolve_seeds,
        )

        # Disk has a ticket
        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        # Bus has a different ticket on the decomposition thread
        capture = WorkflowCapture()
        capture.observe(Utterance(
            thread_id="decomposition",
            speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
            addressed_to="caucus",
            speech_act=SpeechAct.TICKET,
            content=UtteranceContent(
                body="bus body",
                artifacts=[Artifact(kind="ticket", payload={
                    "title": "T-from-bus",
                    "slug": "t-from-bus",
                    "number": 1,
                })],
            ),
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        seeds = resolve_seeds(
            [binding], capture, project_root=tmp_path
        )
        # Only the bus version is present; disk is skipped because
        # bus had results.
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["title"] == "T-from-bus"

    def test_empty_bus_falls_back_to_disk(self, tmp_path: Path) -> None:
        """When the bus is empty for a binding, disk artifacts surface
        as synthetic seed utterances."""
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        seeds = resolve_seeds(
            [binding], self._empty_capture(), project_root=tmp_path
        )
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["title"] == "T-from-disk"

    def test_no_project_root_no_fallback(self, tmp_path: Path) -> None:
        """resolve_seeds called WITHOUT project_root retains the prior
        behavior: empty bus → empty seeds. Back-compat for any caller
        that hasn't wired the new param yet."""
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        # No project_root passed
        seeds = resolve_seeds([binding], self._empty_capture())
        assert seeds == []

    def test_disk_fallback_respects_limit(self, tmp_path: Path) -> None:
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        for i in range(5):
            TicketRegistry(tmp_path).write(TicketPayload(
                title=f"T-{i}",
                owner="tweedledum",
                tier="v1",
                estimate="1 day",
                description="x",
                sources=["s"],
            ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"], "limit": 2}
        )
        seeds = resolve_seeds(
            [binding], self._empty_capture(), project_root=tmp_path
        )
        assert len(seeds) == 2

    def test_disk_fallback_per_item_slicing_works(
        self, tmp_path: Path
    ) -> None:
        """When inside a per_item iteration, disk-loaded artifacts
        for the iteration kind get sliced to the current item's slug.
        Same logic applies to disk content as bus content because
        both end up in the `kinded` list before the slice runs."""
        from wonderland.feature import FeaturePayload, FeatureRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature One",
            description="d",
            tickets=["t1"],
            stack_span="full-stack",
            tier="v1",
            sources=["s"],
        ))
        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature Two",
            description="d",
            tickets=["t2"],
            stack_span="full-stack",
            tier="v1",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "composition", "kinds": ["feature"]}
        )
        seeds = resolve_seeds(
            [binding],
            self._empty_capture(),
            project_root=tmp_path,
            current_item_kind="feature",
            current_item_slug="feature-one",
        )
        # Only the feature-one slice should be present.
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["slug"] == "feature-one"
