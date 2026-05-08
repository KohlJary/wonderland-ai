"""Tests for HistoricalRunHandle.artifacts() — the disk-side view of
artifacts shipped during a run."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from wonderland.observer import HistoricalRunHandle, RunArtifact


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DATA = REPO_ROOT / "analyses" / "data"
_V6_BANNER = ANALYSES_DATA / "029-substrate-convergence" / "v6"


def _require_v6() -> None:
    if not (_V6_BANNER / "wonderland-snapshot").is_dir():
        pytest.skip("v6 banner snapshot not present")


def test_artifacts_returns_run_artifact_instances() -> None:
    _require_v6()
    artifacts = HistoricalRunHandle(_V6_BANNER).artifacts()
    assert all(isinstance(a, RunArtifact) for a in artifacts)


def test_artifacts_sorted_chronologically_ascending() -> None:
    """Reading the list top-to-bottom should be reading the run's
    output stream in the order it was shipped."""
    _require_v6()
    artifacts = HistoricalRunHandle(_V6_BANNER).artifacts()
    timestamps = [a.created_at for a in artifacts]
    assert timestamps == sorted(timestamps)


def test_artifacts_include_expected_kinds_for_v6_banner() -> None:
    """v6 banner should have shipped representative artifacts of each
    major kind: stories, tickets, features, contract_notes, test_scenarios,
    implementations. (Reviews vary; ADRs/rulings depend on the run.)"""
    _require_v6()
    artifacts = HistoricalRunHandle(_V6_BANNER).artifacts()
    kinds = {a.kind for a in artifacts}
    assert "story" in kinds
    assert "ticket" in kinds
    assert "feature" in kinds
    assert "contract_note" in kinds
    assert "test_scenario" in kinds


def test_artifacts_filter_by_kind() -> None:
    _require_v6()
    handle = HistoricalRunHandle(_V6_BANNER)
    features = handle.artifacts(kind="feature")
    assert all(a.kind == "feature" for a in features)
    assert len(features) > 0


def test_artifacts_filter_unknown_kind_returns_empty() -> None:
    _require_v6()
    handle = HistoricalRunHandle(_V6_BANNER)
    assert handle.artifacts(kind="bogus_kind") == []


def test_artifacts_titles_parsed_from_markdown_headings() -> None:
    """Titles should come from the first ``## ItemNNN: Title`` line
    (artifact convention) rather than just the file slug."""
    _require_v6()
    handle = HistoricalRunHandle(_V6_BANNER)
    features = handle.artifacts(kind="feature")
    if not features:
        pytest.skip("v6 has no features")
    # Features in v6 banner: "Start and complete a focus session",
    # "Take a structured break and transition to the next session", etc.
    # The first feature's title should NOT be the slug.
    f = features[0]
    assert f.title != f.path.stem
    # Should be a real title.
    assert len(f.title) > 5


def test_artifacts_filter_count_matches_unfiltered_subset() -> None:
    _require_v6()
    handle = HistoricalRunHandle(_V6_BANNER)
    all_artifacts = handle.artifacts()
    feature_count = sum(1 for a in all_artifacts if a.kind == "feature")
    direct = handle.artifacts(kind="feature")
    assert len(direct) == feature_count


def test_artifacts_paths_point_to_existing_files() -> None:
    """The path on each RunArtifact should be a real file."""
    _require_v6()
    artifacts = HistoricalRunHandle(_V6_BANNER).artifacts()
    for a in artifacts:
        assert a.path.is_file(), f"non-existent file in artifact list: {a.path}"


def test_artifacts_kind_distribution_matches_disk() -> None:
    """Sanity: counting artifacts per kind via the API should match
    counting markdown files in each directory directly."""
    _require_v6()
    handle = HistoricalRunHandle(_V6_BANNER)
    artifacts = handle.artifacts()
    api_counts = Counter(a.kind for a in artifacts)

    # Spot-check stories: count files in stories/ directly.
    stories_dir = _V6_BANNER / "wonderland-snapshot" / "stories"
    if stories_dir.is_dir():
        disk_count = sum(1 for _ in stories_dir.glob("*.md"))
        assert api_counts["story"] == disk_count
