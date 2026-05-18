"""Tests for the T-m8 coverage substrate."""

from __future__ import annotations

from pathlib import Path

from wonderland.coverage import (
    CoverageGap,
    compute_orphan_requirements,
    list_checks,
    register_check,
    run_coverage_check,
)


def _write_req(
    project_root: Path, number: int, slug: str, kind: str
) -> None:
    """Drop a minimal requirement markdown into the project."""
    req_dir = project_root / ".wonderland" / "requirements"
    req_dir.mkdir(parents=True, exist_ok=True)
    path = req_dir / f"requirement-{number:03d}-{slug}.md"
    path.write_text(
        f"## Requirement {number:03d}: {slug}\n\n"
        f"**Slug:** {slug}\n"
        f"**Kind:** {kind}\n"
        f"**Confidence:** operator_stated\n\n"
        f"**Body:**\n\nbody text\n"
    )


def _write_milestone(
    project_root: Path, number: int, slug: str, consumes: list[str]
) -> None:
    """Drop a minimal milestone markdown citing the given requirement slugs."""
    m_dir = project_root / ".wonderland" / "milestones"
    m_dir.mkdir(parents=True, exist_ok=True)
    path = m_dir / f"milestone-{number:02d}-{slug}.md"
    lines = [
        f"## Milestone {number:02d}: {slug}",
        "",
        f"**Slug:** {slug}",
        f"**Order:** {number}",
        "",
        "**Goal:**",
        "",
        "test milestone",
        "",
        "**Consumes requirements:**",
        "",
    ]
    for cslug in consumes:
        lines.append(f"- {cslug}")
    path.write_text("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# requirement_coverage check
# ---------------------------------------------------------------------------


class TestRequirementCoverage:
    def test_returns_none_when_no_requirements(self, tmp_path):
        # No requirements/ dir at all → no gap (nothing to check).
        assert compute_orphan_requirements(tmp_path) is None

    def test_full_coverage_returns_none(self, tmp_path):
        _write_req(tmp_path, 1, "reg-and-auth", "scope")
        _write_req(tmp_path, 2, "equipment-profile", "scope")
        _write_milestone(
            tmp_path, 1, "onboarding",
            consumes=["reg-and-auth", "equipment-profile"],
        )
        assert compute_orphan_requirements(tmp_path) is None

    def test_orphan_requirement_surfaces(self, tmp_path):
        _write_req(tmp_path, 1, "reg-and-auth", "scope")
        _write_req(tmp_path, 2, "equipment-profile", "scope")
        # Only one milestone, only one requirement consumed.
        _write_milestone(
            tmp_path, 1, "onboarding", consumes=["reg-and-auth"]
        )
        gap = compute_orphan_requirements(tmp_path)
        assert gap is not None
        assert gap.check_name == "requirement_coverage"
        assert gap.gap_kind == "orphan_requirements"
        assert gap.items == ("equipment-profile",)

    def test_persona_kind_is_exempt(self, tmp_path):
        """Personas don't decompose into milestones — they inform
        every milestone's stories."""
        _write_req(tmp_path, 1, "marcus-software-developer", "persona")
        # No milestones cite the persona — still no gap.
        assert compute_orphan_requirements(tmp_path) is None

    def test_situation_kind_is_exempt(self, tmp_path):
        _write_req(tmp_path, 1, "marcus-bored-needs-routine", "situation")
        assert compute_orphan_requirements(tmp_path) is None

    def test_out_of_scope_kind_is_exempt(self, tmp_path):
        _write_req(tmp_path, 1, "social-features-deferred", "out_of_scope")
        assert compute_orphan_requirements(tmp_path) is None

    def test_deal_breaker_kind_is_exempt(self, tmp_path):
        _write_req(
            tmp_path, 1, "must-work-offline-or-we-die", "deal_breaker"
        )
        assert compute_orphan_requirements(tmp_path) is None

    def test_constraint_kind_is_decomposable(self, tmp_path):
        """Constraints can be milestone-owned (e.g., a stack-choice
        constraint gates the foundation milestone). Orphaned
        constraints should surface — operator decides whether to
        assign them or note them as cross-cutting."""
        _write_req(tmp_path, 1, "react-frontend-sqlite-backend", "constraint")
        gap = compute_orphan_requirements(tmp_path)
        assert gap is not None
        assert "react-frontend-sqlite-backend" in gap.items

    def test_mixed_kinds_only_flags_decomposable(self, tmp_path):
        _write_req(tmp_path, 1, "marcus-persona", "persona")
        _write_req(tmp_path, 2, "reg-and-auth", "scope")
        _write_req(tmp_path, 3, "deferred", "out_of_scope")
        _write_milestone(
            tmp_path, 1, "ms", consumes=["reg-and-auth"]
        )
        # Persona + out_of_scope are exempt; scope is consumed.
        assert compute_orphan_requirements(tmp_path) is None

    def test_summary_truncates_long_lists(self, tmp_path):
        """Long gap lists get a truncated preview so the nudge body
        stays readable. Full list is still in ``items``."""
        for i in range(8):
            _write_req(tmp_path, i + 1, f"req-{i:02d}", "scope")
        gap = compute_orphan_requirements(tmp_path)
        assert gap is not None
        assert len(gap.items) == 8
        # 5 named inline + "+ 3 more" suffix
        assert "+ 3 more" in gap.summary


# ---------------------------------------------------------------------------
# Registry dispatch
# ---------------------------------------------------------------------------


class TestCheckRegistry:
    def test_list_checks_includes_bundled(self):
        names = list_checks()
        assert "requirement_coverage" in names
        assert "milestone_realization" in names

    def test_unknown_check_returns_none(self, tmp_path):
        assert run_coverage_check("does-not-exist", tmp_path) is None

    def test_register_check_plugs_in(self, tmp_path):
        def my_check(project_root: Path) -> CoverageGap | None:
            return CoverageGap(
                check_name="my_check",
                gap_kind="custom",
                items=("a", "b"),
                summary="2 custom items",
            )

        register_check("my_check", my_check)
        gap = run_coverage_check("my_check", tmp_path)
        assert gap is not None
        assert gap.check_name == "my_check"
        assert gap.items == ("a", "b")

    def test_run_coverage_check_dispatches(self, tmp_path):
        _write_req(tmp_path, 1, "orphan-req", "scope")
        gap = run_coverage_check("requirement_coverage", tmp_path)
        assert gap is not None
        assert gap.items == ("orphan-req",)

    def test_run_coverage_check_swallows_exceptions(self, tmp_path):
        """Coverage is informational — a check that raises shouldn't
        kill the meeting; dispatch returns None silently."""
        def boom(project_root: Path) -> CoverageGap | None:
            raise RuntimeError("intentional")

        register_check("boom", boom)
        assert run_coverage_check("boom", tmp_path) is None


# ---------------------------------------------------------------------------
# milestone_realization check (T-m8b)
# ---------------------------------------------------------------------------


def _write_story(
    project_root: Path,
    number: int,
    slug: str,
    realizes: list[str],
) -> None:
    """Write a minimal story markdown with the realizes_requirements
    section the parser reads."""
    d = project_root / ".wonderland" / "stories"
    d.mkdir(parents=True, exist_ok=True)
    realizes_block = (
        "\n".join(f"- {r}" for r in realizes) if realizes else "- —"
    )
    (d / f"story-{number:03d}-{slug}.md").write_text(
        f"## Story {number:03d}: {slug}\n\n"
        f"**Persona:** marcus\n\n"
        f"**Realizes requirements:**\n{realizes_block}\n"
    )


def _write_feature(
    project_root: Path, number: int, slug: str, sources: list[str]
) -> None:
    """Write a minimal feature markdown citing the given story slugs
    as its sources."""
    d = project_root / ".wonderland" / "features"
    d.mkdir(parents=True, exist_ok=True)
    src_line = ", ".join(sources) if sources else "—"
    (d / f"feature-{number:03d}-{slug}.md").write_text(
        f"## Feature {number:03d}: {slug}\n\n"
        f"**Sources:** {src_line}\n"
    )


class TestMilestoneRealization:
    """T-m8b: a milestone's consumes_requirements are realized when
    each one has at least one story citing it in realizes_requirements
    AND a feature sourcing that story."""

    def test_returns_none_when_no_milestone_slug(self, tmp_path):
        assert (
            run_coverage_check(
                "milestone_realization", tmp_path, milestone_slug=None
            )
            is None
        )

    def test_returns_none_when_milestone_not_found(self, tmp_path):
        gap = run_coverage_check(
            "milestone_realization",
            tmp_path,
            milestone_slug="ghost-milestone",
        )
        assert gap is None

    def test_full_realization_returns_none(self, tmp_path):
        _write_req(tmp_path, 1, "req-a", "integration")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        _write_story(tmp_path, 1, "marcus-uses-a", realizes=["req-a"])
        _write_feature(
            tmp_path, 1, "marcus-feature", sources=["marcus-uses-a"]
        )
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is None

    def test_unrealized_requirement_surfaces(self, tmp_path):
        _write_req(tmp_path, 1, "req-a", "integration")
        _write_req(tmp_path, 2, "req-b", "integration")
        _write_milestone(
            tmp_path, 1, "m1", consumes=["req-a", "req-b"]
        )
        _write_story(tmp_path, 1, "story-a", realizes=["req-a"])
        _write_feature(tmp_path, 1, "feat-a", sources=["story-a"])
        # req-b has no story/feature chain — unrealized.
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is not None
        assert gap.items == ("req-b",)
        assert gap.check_name == "milestone_realization"

    def test_story_without_feature_counts_as_unrealized(self, tmp_path):
        """Story alone isn't enough — M2's job is features, and the
        coverage gate is feature-level."""
        _write_req(tmp_path, 1, "req-a", "integration")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        _write_story(tmp_path, 1, "story-a", realizes=["req-a"])
        # No feature sourcing story-a.
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is not None
        assert gap.items == ("req-a",)

    def test_feature_without_realizing_story_doesnt_help(self, tmp_path):
        """A feature sourcing a story that doesn't realize the
        requirement leaves the requirement unrealized — the link is
        through realizes_requirements, not feature presence."""
        _write_req(tmp_path, 1, "req-a", "integration")
        _write_milestone(tmp_path, 1, "m1", consumes=["req-a"])
        _write_story(tmp_path, 1, "unrelated-story", realizes=[])
        _write_feature(
            tmp_path, 1, "feat", sources=["unrelated-story"]
        )
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is not None
        assert "req-a" in gap.items

    def test_summary_truncates_long_lists(self, tmp_path):
        for i in range(8):
            slug = f"req-{i:02d}"
            _write_req(tmp_path, i + 1, slug, "integration")
        _write_milestone(
            tmp_path, 1, "m1",
            consumes=[f"req-{i:02d}" for i in range(8)],
        )
        # No stories / features at all — every req is unrealized.
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is not None
        assert len(gap.items) == 8
        assert "+ 3 more" in gap.summary

    def test_persona_consumes_are_exempt_from_realization(
        self, tmp_path
    ):
        """When Rabbit's milestone-plan includes a persona-kind
        requirement in consumes (which happens when the milestone
        is named for its primary persona), M2 shouldn't have to
        ship a feature realizing a persona — those are context."""
        _write_req(tmp_path, 1, "marcus-persona", "persona")
        _write_req(tmp_path, 2, "register-and-auth", "integration")
        _write_milestone(
            tmp_path, 1, "m1",
            consumes=["marcus-persona", "register-and-auth"],
        )
        _write_story(
            tmp_path, 1, "marcus-registers",
            realizes=["register-and-auth"],
        )
        _write_feature(
            tmp_path, 1, "onboarding", sources=["marcus-registers"]
        )
        # Persona consume isn't checked for realization; the
        # success_criterion IS realized. Should report no gap.
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is None

    def test_situation_and_out_of_scope_consumes_are_exempt(self, tmp_path):
        _write_req(tmp_path, 1, "marcus-bored", "situation")
        _write_req(tmp_path, 2, "social-deferred", "out_of_scope")
        _write_req(tmp_path, 3, "register-and-auth", "integration")
        _write_milestone(
            tmp_path, 1, "m1",
            consumes=[
                "marcus-bored",
                "social-deferred",
                "register-and-auth",
            ],
        )
        _write_story(
            tmp_path, 1, "marcus-registers",
            realizes=["register-and-auth"],
        )
        _write_feature(
            tmp_path, 1, "onboarding", sources=["marcus-registers"]
        )
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is None

    def test_scope_and_constraint_consumes_are_exempt_from_realization(
        self, tmp_path
    ):
        """Mvp-demo regression: ``scope`` and ``constraint`` kinds
        kept generating phantom coverage gaps. ``v1 has no auth``
        (scope) and ``backend availability is hard`` (constraint)
        are meta-statements about the system, not features to
        build — they shouldn't be flagged as unrealized when
        consumed by a milestone.

        Stale-scope/constraint entries in milestones' consumes
        wedged 22-rotation design loops in mvp-demo M2/M3 design
        passes (agents correctly diagnosed the structural problem
        but had no path forward)."""
        _write_req(tmp_path, 1, "v1-no-auth", "scope")
        _write_req(tmp_path, 2, "backend-availability", "constraint")
        _write_req(tmp_path, 3, "v1-ships-when-clone-runs", "success_criterion")
        _write_req(tmp_path, 4, "register-and-auth", "integration")
        _write_milestone(
            tmp_path, 1, "m1",
            consumes=[
                "v1-no-auth",
                "backend-availability",
                "v1-ships-when-clone-runs",
                "register-and-auth",
            ],
        )
        _write_story(
            tmp_path, 1, "marcus-registers",
            realizes=["register-and-auth"],
        )
        _write_feature(
            tmp_path, 1, "onboarding", sources=["marcus-registers"]
        )
        # scope + constraint + success_criterion all exempt from
        # realization check; only integration needs feature
        # realization, and it has one. No gap should report.
        gap = run_coverage_check(
            "milestone_realization", tmp_path, milestone_slug="m1"
        )
        assert gap is None


# ---------- minimum_stories check (P16 — M1 deadlock backup) ----------


class TestMinimumStoriesCheck:
    """The validation2 pilots showed M1 can deadlock with zero or
    one stories shipped even with the explicit lead-assignment
    framing block. minimum_stories is the substrate's belt-and-
    suspenders guarantee: rotation budget extends until at least
    3 stories ship (or extra-rotations cap exhausts)."""

    def test_no_stories_dir_returns_gap(self, tmp_path: Path) -> None:
        """Fresh project, M1 hasn't shipped anything yet — gap
        with count=0 in the summary."""
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is not None
        assert gap.check_name == "minimum_stories"
        assert gap.gap_kind == "insufficient_stories"
        assert "0 story" in gap.summary

    def test_empty_stories_dir_returns_gap(self, tmp_path: Path) -> None:
        """Directory exists but no story files — same gap shape."""
        (tmp_path / ".wonderland" / "stories").mkdir(parents=True)
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is not None
        assert "0 story" in gap.summary

    def test_one_story_returns_gap_with_count(self, tmp_path: Path) -> None:
        """Below threshold — gap summary names the count so agents
        see how many more are needed before next rotation fires."""
        _write_story(tmp_path, 1, "only-story", realizes=[])
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is not None
        assert "1 story" in gap.summary
        assert "2 more" in gap.summary

    def test_two_stories_still_below_threshold(self, tmp_path: Path) -> None:
        _write_story(tmp_path, 1, "story-a", realizes=[])
        _write_story(tmp_path, 2, "story-b", realizes=[])
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is not None
        assert "1 more" in gap.summary

    def test_exactly_three_stories_closes_gap(self, tmp_path: Path) -> None:
        for i, slug in enumerate(["a", "b", "c"], start=1):
            _write_story(tmp_path, i, f"story-{slug}", realizes=[])
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is None

    def test_more_than_three_stories_no_gap(self, tmp_path: Path) -> None:
        """The check is a floor, not a ceiling."""
        for i, slug in enumerate(["a", "b", "c", "d", "e"], start=1):
            _write_story(tmp_path, i, f"story-{slug}", realizes=[])
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is None

    def test_gap_summary_names_lead_handoff(self, tmp_path: Path) -> None:
        """The substrate's nudge cites the M1 LEAD framing block so
        whichever agent's the lead picks up the directive cleanly —
        not a generic 'someone ship more' nudge."""
        gap = run_coverage_check("minimum_stories", tmp_path)
        assert gap is not None
        assert "M1 LEAD" in gap.summary
        assert "decision: story" in gap.summary
