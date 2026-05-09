"""Tests for HistoricalRunHandle — uses real snapshot fixtures from
``analyses/data/``.

Per the P8.1 design: snapshots double as test fixtures. Every UI
view should be validatable against a chosen historical run; the
test suite's job is to pin the read API behavior on those same
fixtures.

Primary fixture: ``analyses/data/029-substrate-convergence/v6/`` —
the substrate banner run with all meetings completed end-to-end and
real test signal. Secondary fixtures used to pin edge cases
(MEETING_BUDGET, M5 RUNNING, etc.) as needed.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from wonderland.observer import (
    AgentTelemetry,
    HistoricalRunHandle,
    RunMeeting,
    RunSummary,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSES_DATA = REPO_ROOT / "analyses" / "data"


# Snapshot fixtures we expect on disk. Skipping a test if its fixture
# isn't present (e.g. someone running tests on a partial checkout)
# beats failing — the test suite shouldn't depend on the analyses
# directory's exact contents.
_V6_BANNER = ANALYSES_DATA / "029-substrate-convergence" / "v6"
_V8_BANNER = ANALYSES_DATA / "030-directive-bounds" / "v8"


def _require_snapshot(path: Path) -> None:
    if not (path / "wonderland-snapshot").is_dir():
        pytest.skip(f"snapshot fixture not present: {path}")
    if not (path / "run.log").is_file():
        pytest.skip(f"snapshot fixture missing run.log: {path}")


# ---------- construction + shape validation ----------


def test_rejects_missing_snapshot_dir(tmp_path: Path) -> None:
    """A directory without wonderland-snapshot/ should fail fast."""
    (tmp_path / "run.log").write_text("hello\n")
    with pytest.raises(FileNotFoundError, match="wonderland-snapshot"):
        HistoricalRunHandle(tmp_path)


def test_run_log_now_optional_for_tui_layouts(tmp_path: Path) -> None:
    """Pre-T58d behavior required run.log; TUI runs don't write it
    (yet), so HistoricalRunHandle now accepts the wonderland-snapshot
    or .wonderland directory alone. summary() degrades gracefully:
    directive/workflow_name come back None but the handle constructs
    cleanly so the snapshot library can list it."""
    (tmp_path / "wonderland-snapshot").mkdir()
    handle = HistoricalRunHandle(tmp_path)
    summary = handle.summary()
    assert summary.directive is None
    assert summary.workflow_name is None
    assert summary.project_root == tmp_path


def test_accepts_dot_wonderland_layout(tmp_path: Path) -> None:
    """TUI runs use ``.wonderland/`` instead of ``wonderland-snapshot/``;
    HistoricalRunHandle accepts both."""
    (tmp_path / ".wonderland").mkdir()
    handle = HistoricalRunHandle(tmp_path)
    summary = handle.summary()
    assert summary.project_root == tmp_path


def test_constructs_against_v6_banner() -> None:
    _require_snapshot(_V6_BANNER)
    handle = HistoricalRunHandle(_V6_BANNER)
    assert handle.snapshot_dir == _V6_BANNER


# ---------- summary ----------


def test_summary_extracts_workflow_directive_project_root() -> None:
    _require_snapshot(_V6_BANNER)
    s = HistoricalRunHandle(_V6_BANNER).summary()
    assert isinstance(s, RunSummary)
    assert s.workflow_name == "tdd"
    # Pomodoro directive — head + verification it's not empty / truncated.
    assert s.directive is not None
    assert "pomodoro" in s.directive.lower()
    assert s.project_root is not None


def test_summary_total_cost_matches_telemetry() -> None:
    """v6 banner is documented in analysis 029 at $4.24 total."""
    _require_snapshot(_V6_BANNER)
    s = HistoricalRunHandle(_V6_BANNER).summary()
    # Don't pin to exact penny — float-precision tolerance.
    assert 4.0 < s.total_cost < 4.5
    assert s.total_calls > 200


def test_summary_started_and_ended_times_present() -> None:
    """Timestamps come from the first/last utterance in Dodo's memory."""
    _require_snapshot(_V6_BANNER)
    s = HistoricalRunHandle(_V6_BANNER).summary()
    assert s.started_at is not None
    assert s.ended_at is not None
    assert isinstance(s.started_at, datetime)
    assert s.ended_at >= s.started_at


# ---------- meetings ----------


def test_meetings_returns_seven_for_tdd_run() -> None:
    """TDD workflow has M1-M6 + M2.5 = 7 meetings."""
    _require_snapshot(_V6_BANNER)
    meetings = HistoricalRunHandle(_V6_BANNER).meetings()
    assert len(meetings) == 7
    labels = [m.label for m in meetings]
    assert labels == ["M1", "M2", "M2.5", "M3", "M4", "M5", "M6"]


def test_meetings_carry_book_event_names() -> None:
    """Per analysis 028: meetings have name fields rendering in logs."""
    _require_snapshot(_V6_BANNER)
    meetings = HistoricalRunHandle(_V6_BANNER).meetings()
    by_label = {m.label: m for m in meetings}
    assert by_label["M1"].name == "The Caucus Race"
    assert by_label["M2.5"].name == "Advice from a Caterpillar"
    assert by_label["M4"].name == "The Mad Tea Party"
    assert by_label["M6"].name == "The Trial"
    # M5 is intentionally unnamed (heads-down implementation work).
    assert by_label["M5"].name is None


def test_meetings_have_outcomes_and_costs() -> None:
    _require_snapshot(_V6_BANNER)
    meetings = HistoricalRunHandle(_V6_BANNER).meetings()
    for m in meetings:
        assert isinstance(m, RunMeeting)
        assert m.outcome is not None  # banner has all meetings ended
        assert m.cost >= 0.0
        assert m.calls >= 0
        assert m.elapsed_seconds is not None


def test_meetings_thread_id_matches_workflow_yaml() -> None:
    """Meeting.id should match the YAML's `id` field, not the label."""
    _require_snapshot(_V6_BANNER)
    meetings = HistoricalRunHandle(_V6_BANNER).meetings()
    by_label = {m.label: m for m in meetings}
    assert by_label["M1"].id == "scoping"
    assert by_label["M2"].id == "decomposition"
    assert by_label["M2.5"].id == "composition"
    assert by_label["M3"].id == "contract-negotiation"
    assert by_label["M4"].id == "test-scenarios"
    assert by_label["M5"].id == "implementation"
    assert by_label["M6"].id == "review"


# ---------- utterances ----------


def test_utterances_yields_in_chronological_order() -> None:
    _require_snapshot(_V6_BANNER)
    handle = HistoricalRunHandle(_V6_BANNER)
    timestamps = [u.timestamp for u in handle.utterances()]
    assert timestamps  # not empty
    assert timestamps == sorted(timestamps)


def test_utterances_filtered_by_thread_id_only_returns_that_thread() -> None:
    _require_snapshot(_V6_BANNER)
    handle = HistoricalRunHandle(_V6_BANNER)
    scoping_utterances = list(handle.utterances(thread_id="scoping"))
    assert len(scoping_utterances) > 0
    assert all(u.thread_id == "scoping" for u in scoping_utterances)


def test_utterances_filter_subset_of_total() -> None:
    """Filtering to one thread should give fewer utterances than no filter."""
    _require_snapshot(_V6_BANNER)
    handle = HistoricalRunHandle(_V6_BANNER)
    total = sum(1 for _ in handle.utterances())
    scoping_only = sum(1 for _ in handle.utterances(thread_id="scoping"))
    assert scoping_only < total


# ---------- per-agent telemetry ----------


def test_per_agent_telemetry_returns_all_cast_members() -> None:
    """Banner runs exercise the full cast — all 8 character agents
    plus the dodo should show up. Telemetry tracks the 8 LLM-using
    characters (dodo's procedural moves don't make LLM calls)."""
    _require_snapshot(_V6_BANNER)
    handle = HistoricalRunHandle(_V6_BANNER)
    telemetry = handle.per_agent_telemetry()
    names = {t.name for t in telemetry}
    expected_characters = {
        "alice",
        "cheshire_cat",
        "queen_of_hearts",
        "white_rabbit",
        "mad_hatter",
        "tweedledee",
        "tweedledum",
        "caterpillar",
    }
    assert expected_characters.issubset(names)


def test_per_agent_telemetry_sorted_by_cost_desc() -> None:
    _require_snapshot(_V6_BANNER)
    telemetry = HistoricalRunHandle(_V6_BANNER).per_agent_telemetry()
    costs = [t.cost for t in telemetry]
    assert costs == sorted(costs, reverse=True)


def test_per_agent_telemetry_tweedles_dominate_in_v6() -> None:
    """v6 had Tweedles eating most of the budget (analysis 029).
    A useful sanity check the data round-trips correctly."""
    _require_snapshot(_V6_BANNER)
    telemetry = HistoricalRunHandle(_V6_BANNER).per_agent_telemetry()
    assert isinstance(telemetry[0], AgentTelemetry)
    # Top-cost agent should be one of the Tweedles in v6
    assert telemetry[0].name in ("tweedledum", "tweedledee")


# ---------- v8 cross-fixture sanity check ----------


def test_v8_snapshot_also_loads() -> None:
    """Pin that the API works against another fixture — v8 banner."""
    _require_snapshot(_V8_BANNER)
    handle = HistoricalRunHandle(_V8_BANNER)
    s = handle.summary()
    assert s.workflow_name == "tdd"
    meetings = handle.meetings()
    assert len(meetings) == 7
    assert all(m.outcome is not None for m in meetings)
