"""Tests for milestone-close consolidation of episodic memory branches.

T-a2 chunk C — verifies the consolidate_milestone orchestrator
correctly archives design+impl branches across per-agent stores and
records a project-level summary utterance.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland import EpisodicStore
from wonderland.memory.consolidation import consolidate_milestone
from wonderland.memory.episodic import (
    ARCHIVED_PREFIX,
    PROJECT_BRANCH,
    inheritance_chain,
    reset_active_branch_id,
    set_active_branch_id,
)
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


def _utterance(body: str) -> Utterance:
    return Utterance(
        thread_id="t",
        speaker=AgentIdentity(name="cheshire_cat", constitution_version="0.1"),
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body=body, artifacts=[]),
    )


pytestmark = pytest.mark.asyncio


async def _seed_agent_memory(
    project_root: Path,
    agent: str,
    branch_to_bodies: dict[str, list[str]],
) -> None:
    """Record utterances under multiple branches for one agent."""
    async with EpisodicStore(project_root, agent) as store:
        for branch, bodies in branch_to_bodies.items():
            token = set_active_branch_id(branch)
            try:
                for body in bodies:
                    await store.record(_utterance(body))
            finally:
                reset_active_branch_id(token)


async def test_consolidate_archives_design_and_impl_branches(
    tmp_path: Path,
) -> None:
    """After consolidation, design:<slug> and impl:<slug> branches
    get rewritten to archived:design:<slug> + archived:impl:<slug>.
    Project-level summary utterance lands on PROJECT_BRANCH."""
    await _seed_agent_memory(tmp_path, "alice", {
        "design:m1-foo": ["m1-design-1", "m1-design-2"],
        "impl:m1-foo": ["m1-impl-1"],
        PROJECT_BRANCH: ["pre-existing-project"],
    })

    results = await consolidate_milestone(
        tmp_path,
        milestone_slug="m1-foo",
        milestone_name="Foundation",
        feature_slugs=["feat-a", "feat-b"],
    )

    assert results == {"alice": 3}  # 2 design + 1 impl archived

    # Verify on-disk state
    async with EpisodicStore(tmp_path, "alice") as store:
        # Original design branch is empty (rewritten)
        design = await store.query_by_thread(
            "t", branches=["design:m1-foo"]
        )
        assert len(design) == 0
        impl = await store.query_by_thread(
            "t", branches=["impl:m1-foo"]
        )
        assert len(impl) == 0
        # Archived versions hold the original utterances
        archived_design = await store.query_by_thread(
            "t", branches=[f"{ARCHIVED_PREFIX}design:m1-foo"]
        )
        assert [u.content.body for u in archived_design] == [
            "m1-design-1", "m1-design-2",
        ]
        archived_impl = await store.query_by_thread(
            "t", branches=[f"{ARCHIVED_PREFIX}impl:m1-foo"]
        )
        assert [u.content.body for u in archived_impl] == ["m1-impl-1"]
        # Project branch has the pre-existing utterance + summary
        project = await store.query_by_thread(
            "t", branches=[PROJECT_BRANCH]
        )
        # Pre-existing on thread 't'
        assert any(u.content.body == "pre-existing-project" for u in project)
    # Summary lands on a different thread (milestone-consolidation)
    async with EpisodicStore(tmp_path, "alice") as store:
        summary = await store.query_by_thread(
            "milestone-consolidation", branches=[PROJECT_BRANCH]
        )
        assert len(summary) == 1
        body = summary[0].content.body
        assert "m1-foo" in body
        assert "Foundation" in body
        assert "feat-a" in body
        assert "feat-b" in body
        assert summary[0].speaker.name == "mock_turtle"


async def test_consolidate_fires_across_all_agents(tmp_path: Path) -> None:
    """consolidate_milestone iterates every per-agent store."""
    await _seed_agent_memory(tmp_path, "alice", {
        "design:m1": ["alice-design"],
    })
    await _seed_agent_memory(tmp_path, "white_rabbit", {
        "design:m1": ["rabbit-design-1", "rabbit-design-2"],
        "impl:m1": ["rabbit-impl"],
    })
    await _seed_agent_memory(tmp_path, "caterpillar", {
        # No m1 branches — only project
        PROJECT_BRANCH: ["cat-misc"],
    })

    results = await consolidate_milestone(
        tmp_path,
        milestone_slug="m1",
        feature_slugs=["x"],
    )

    assert results == {
        "alice": 1,
        "white_rabbit": 3,
        "caterpillar": 0,  # nothing to archive but summary still written
    }
    # Caterpillar still gets the summary
    async with EpisodicStore(tmp_path, "caterpillar") as store:
        summary = await store.query_by_thread(
            "milestone-consolidation", branches=[PROJECT_BRANCH]
        )
        assert len(summary) == 1


async def test_inheritance_chain_excludes_archived(tmp_path: Path) -> None:
    """The whole point: after consolidation, future agent reads via
    inheritance_chain see the summary but NOT the archived churn.
    This is the wedge-bleed-prevention check."""
    await _seed_agent_memory(tmp_path, "alice", {
        "design:m1": ["m1-wedge-noise-1", "m1-wedge-noise-2"],
    })

    await consolidate_milestone(
        tmp_path,
        milestone_slug="m1",
        feature_slugs=["feat-x"],
    )

    # Simulate M2 design agent reading via inheritance chain
    async with EpisodicStore(tmp_path, "alice") as store:
        token = set_active_branch_id("design:m2")
        try:
            # M2 agent reads project + m2 branches.
            # On thread 't': M1's archived churn must NOT show up.
            m2_view_t = await store.query_by_thread(
                "t", branches=inheritance_chain("design:m2"),
            )
            bodies = [u.content.body for u in m2_view_t]
            assert "m1-wedge-noise-1" not in bodies
            assert "m1-wedge-noise-2" not in bodies

            # On the consolidation thread: M2 agent SEES the summary
            m2_view_summary = await store.query_by_thread(
                "milestone-consolidation",
                branches=inheritance_chain("design:m2"),
            )
            assert len(m2_view_summary) == 1
            assert "m1" in m2_view_summary[0].content.body
        finally:
            reset_active_branch_id(token)


async def test_consolidate_with_no_agent_dirs_is_noop(
    tmp_path: Path,
) -> None:
    """Empty memory dir → consolidation returns empty dict, no crash."""
    results = await consolidate_milestone(
        tmp_path,
        milestone_slug="m1",
        feature_slugs=[],
    )
    assert results == {}


async def test_consolidate_idempotent_on_already_archived(
    tmp_path: Path,
) -> None:
    """Re-running consolidation on an already-archived branch:
    archive_branch returns 0 rows rewritten; no error."""
    await _seed_agent_memory(tmp_path, "alice", {
        "design:m1": ["first"],
    })

    first = await consolidate_milestone(
        tmp_path,
        milestone_slug="m1",
        feature_slugs=["x"],
    )
    assert first == {"alice": 1}

    second = await consolidate_milestone(
        tmp_path,
        milestone_slug="m1",
        feature_slugs=["x"],
    )
    # Branches already archived → 0 archived this round
    assert second == {"alice": 0}
