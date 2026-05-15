"""Tests for the P15 T-m8 project-phase derivation."""

from __future__ import annotations

from pathlib import Path

from wonderland.project import (
    ProjectPhase,
    derive_project_phase,
)


# ---------------------------------------------------------------------------
# Helpers — minimal disk fixtures
# ---------------------------------------------------------------------------


def _write_req(root: Path, number: int, slug: str, kind: str) -> None:
    d = root / ".wonderland" / "requirements"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"requirement-{number:03d}-{slug}.md").write_text(
        f"## Requirement {number:03d}: {slug}\n\n"
        f"**Slug:** {slug}\n"
        f"**Kind:** {kind}\n"
        f"**Confidence:** operator_stated\n\n"
        f"**Body:**\n\nbody\n"
    )


def _write_milestone(
    root: Path, number: int, slug: str, consumes: list[str]
) -> None:
    d = root / ".wonderland" / "milestones"
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"## Milestone {number:02d}: {slug}",
        "",
        f"**Slug:** {slug}",
        f"**Order:** {number}",
        "",
        "**Goal:**",
        "",
        "test",
        "",
        "**Consumes requirements:**",
        "",
    ]
    for c in consumes:
        lines.append(f"- {c}")
    (d / f"milestone-{number:02d}-{slug}.md").write_text(
        "\n".join(lines) + "\n"
    )


def _write_story(
    root: Path, number: int, slug: str, realizes: list[str]
) -> None:
    d = root / ".wonderland" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    realizes_block = (
        "\n".join(f"- {r}" for r in realizes) if realizes else "- —"
    )
    (d / f"story-{number:03d}-{slug}.md").write_text(
        f"## Story {number:03d}: {slug}\n\n"
        f"**Realizes requirements:**\n{realizes_block}\n"
    )


def _write_feature(
    root: Path, number: int, slug: str, sources: list[str]
) -> None:
    d = root / ".wonderland" / "features"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"feature-{number:03d}-{slug}.md").write_text(
        f"## Feature {number:03d}: {slug}\n\n"
        f"**Sources:** {', '.join(sources)}\n"
    )


# ---------------------------------------------------------------------------
# Phase derivation
# ---------------------------------------------------------------------------


class TestDeriveProjectPhase:
    def test_no_wland_dir_returns_discovery(self, tmp_path: Path):
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.DISCOVERY
        assert "no requirements" in snap.label.lower()
        assert "discovery" in snap.next_action_hint.lower()
        assert snap.requirements_count == 0

    def test_no_requirements_returns_discovery(self, tmp_path: Path):
        (tmp_path / ".wonderland").mkdir()
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.DISCOVERY

    def test_requirements_without_milestones_returns_planning(
        self, tmp_path: Path
    ):
        _write_req(tmp_path, 1, "req-a", "scope")
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.PLANNING
        assert "milestone-plan" in snap.next_action_hint
        assert snap.requirements_count == 1
        assert snap.milestones_count == 0

    def test_milestones_without_features_returns_design(
        self, tmp_path: Path
    ):
        _write_req(tmp_path, 1, "req-a", "scope")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.DESIGN
        # m1 is undesigned (no stories, no features) — recommended.
        assert "m1" in snap.next_action_hint
        assert "tdd-design" in snap.next_action_hint

    def test_design_advances_to_next_undesigned_milestone(
        self, tmp_path: Path
    ):
        """When M1 is fully realized but M2 isn't, the phase
        recommendation points at M2."""
        _write_req(tmp_path, 1, "req-a", "scope")
        _write_req(tmp_path, 2, "req-b", "scope")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        _write_milestone(tmp_path, 2, "m2", consumes=["req-b"])
        _write_story(tmp_path, 1, "story-a", realizes=["req-a"])
        _write_feature(tmp_path, 1, "feat-a", sources=["story-a"])
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.DESIGN
        assert "m2" in snap.next_action_hint
        assert snap.designed_milestones_count == 1
        assert snap.milestones_count == 2

    def test_all_milestones_designed_returns_implementation(
        self, tmp_path: Path
    ):
        _write_req(tmp_path, 1, "req-a", "scope")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        _write_story(tmp_path, 1, "story-a", realizes=["req-a"])
        _write_feature(tmp_path, 1, "feat-a", sources=["story-a"])
        snap = derive_project_phase(tmp_path)
        assert snap.phase is ProjectPhase.IMPLEMENTATION
        assert "tdd-implement" in snap.next_action_hint
        assert snap.designed_milestones_count == 1
