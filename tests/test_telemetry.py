"""Tests for token telemetry — pricing math + aggregation + JSON roundtrip."""

from __future__ import annotations

import json
from pathlib import Path

from wonderland import TokenUsage
from wonderland.telemetry import (
    HAIKU_4_5_CACHE_READ_PER_MTOK,
    HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK,
    HAIKU_4_5_INPUT_PER_MTOK,
    HAIKU_4_5_OUTPUT_PER_MTOK,
    Telemetry,
    estimate_cost,
    get_current_thread_id,
    reset_current_thread_id,
    set_current_thread_id,
)

# --------------------------------------------------------------------- #
# Pricing
# --------------------------------------------------------------------- #


def test_pricing_constants_match_published_haiku_4_5() -> None:
    """Sanity check the constants match the public docs.

    If Anthropic changes prices, these tests fail loudly so we update
    the constants and the reference_haiku_pricing memory together.
    """
    assert HAIKU_4_5_INPUT_PER_MTOK == 1.00
    assert HAIKU_4_5_OUTPUT_PER_MTOK == 5.00
    assert HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK == 1.25
    assert HAIKU_4_5_CACHE_READ_PER_MTOK == 0.10


def test_estimate_cost_uncached_input_only() -> None:
    usage = TokenUsage(input_tokens=1_000_000, output_tokens=0)
    assert estimate_cost(usage) == 1.00


def test_estimate_cost_output_only() -> None:
    usage = TokenUsage(input_tokens=0, output_tokens=1_000_000)
    assert estimate_cost(usage) == 5.00


def test_estimate_cost_cache_read_is_one_tenth_input() -> None:
    usage = TokenUsage(cache_read_input_tokens=1_000_000)
    assert estimate_cost(usage) == 0.10


def test_estimate_cost_cache_write_is_one_and_a_quarter_input() -> None:
    usage = TokenUsage(cache_creation_input_tokens=1_000_000)
    assert estimate_cost(usage) == 1.25


def test_estimate_cost_combines_all_four_components() -> None:
    """Sanity: the formula matches what the dashboard charges."""
    usage = TokenUsage(
        input_tokens=100_000,
        output_tokens=20_000,
        cache_creation_input_tokens=50_000,
        cache_read_input_tokens=200_000,
    )
    expected = (
        100_000 * 1.00 / 1_000_000
        + 20_000 * 5.00 / 1_000_000
        + 50_000 * 1.25 / 1_000_000
        + 200_000 * 0.10 / 1_000_000
    )
    assert abs(estimate_cost(usage) - expected) < 1e-9


def test_estimate_cost_full_cast_run_matches_post_hoc_calc() -> None:
    """The full-cast race in analysis 006 (post T32 + T33 re-run) cost
    ~$8-9 per the dashboard. Sanity: the formula gets us into that range."""
    # Numbers from the actual run captured in /tmp/full-cast-2.txt
    usage = TokenUsage(
        input_tokens=8_314_725,
        output_tokens=140_086,
        cache_creation_input_tokens=86_351,
        cache_read_input_tokens=2_850_548,
    )
    cost = estimate_cost(usage)
    assert 8.0 <= cost <= 10.0


# --------------------------------------------------------------------- #
# Telemetry aggregation
# --------------------------------------------------------------------- #


def test_telemetry_records_per_call_and_aggregates() -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000, output_tokens=200))
    tel.record("alice", TokenUsage(input_tokens=2000, output_tokens=400))
    tel.record("cheshire_cat", TokenUsage(input_tokens=500, output_tokens=100))

    assert tel.call_count == 3
    summary = tel.per_agent_summary()
    assert summary["alice"]["calls"] == 2
    assert summary["alice"]["input_tokens"] == 3000
    assert summary["alice"]["output_tokens"] == 600
    assert summary["cheshire_cat"]["calls"] == 1
    assert summary["cheshire_cat"]["input_tokens"] == 500


def test_telemetry_total_cost_is_running_sum() -> None:
    tel = Telemetry()
    cost1 = estimate_cost(TokenUsage(input_tokens=1000))
    cost2 = estimate_cost(TokenUsage(output_tokens=200))
    tel.record("alice", TokenUsage(input_tokens=1000))
    assert tel.total_cost == cost1
    tel.record("cheshire_cat", TokenUsage(output_tokens=200))
    assert tel.total_cost == cost1 + cost2


def test_record_for_returns_callback_attributing_to_agent() -> None:
    tel = Telemetry()
    cb = tel.record_for("alice")
    cb(TokenUsage(input_tokens=1000))
    assert tel.entries[0].agent == "alice"


def test_telemetry_per_agent_cost_in_summary() -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1_000_000))  # $1.00
    tel.record("cheshire_cat", TokenUsage(output_tokens=200_000))  # $1.00
    summary = tel.per_agent_summary()
    assert abs(float(summary["alice"]["cost"]) - 1.00) < 0.01
    assert abs(float(summary["cheshire_cat"]["cost"]) - 1.00) < 0.01


# --------------------------------------------------------------------- #
# Run record JSON
# --------------------------------------------------------------------- #


def test_write_run_record_creates_directory_and_file(tmp_path: Path) -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000, output_tokens=200))
    path = tel.write_run_record(tmp_path, "test-001")
    assert path == tmp_path / ".wonderland" / "telemetry" / "run-test-001.json"
    assert path.is_file()


def test_run_record_contains_pricing_and_totals(tmp_path: Path) -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000, output_tokens=200))
    path = tel.write_run_record(tmp_path, "x")
    record = json.loads(path.read_text())
    assert record["run_id"] == "x"
    assert record["model"] == "claude-haiku-4-5-20251001"
    assert record["pricing_per_mtok"]["input"] == 1.00
    assert record["pricing_per_mtok"]["output"] == 5.00
    assert record["total_calls"] == 1
    assert record["total_cost"] > 0
    assert "alice" in record["per_agent"]


def test_run_record_includes_extra_metadata(tmp_path: Path) -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000))
    path = tel.write_run_record(
        tmp_path,
        "x",
        extra={"outcome": "complete", "elapsed_seconds": 42.5},
    )
    record = json.loads(path.read_text())
    assert record["outcome"] == "complete"
    assert record["elapsed_seconds"] == 42.5


def test_run_record_entries_match_recorded_usage(tmp_path: Path) -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000, output_tokens=200))
    tel.record("cheshire_cat", TokenUsage(input_tokens=500, cache_read_input_tokens=100))
    path = tel.write_run_record(tmp_path, "x")
    record = json.loads(path.read_text())
    assert len(record["entries"]) == 2
    assert record["entries"][0]["agent"] == "alice"
    assert record["entries"][0]["input_tokens"] == 1000
    assert record["entries"][1]["agent"] == "cheshire_cat"
    assert record["entries"][1]["cache_read_input_tokens"] == 100


# --------------------------------------------------------------------- #
# Per-thread cost (parallel meeting fix — May 10 cost-attribution bug)
# --------------------------------------------------------------------- #


def test_thread_id_default_is_empty_string() -> None:
    """No context set → empty thread_id, no per-thread accounting."""
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000))
    assert get_current_thread_id() == ""
    # Empty thread_id doesn't accumulate to per_thread_cost so an
    # outside-meeting setup call can't bleed into a meeting's budget.
    assert tel.cost_for_thread("") == 0.0
    assert tel.entries[0].thread_id == ""


def test_record_attributes_to_current_thread_id() -> None:
    tel = Telemetry()
    token = set_current_thread_id("m5-feature-a")
    try:
        tel.record("tweedledee", TokenUsage(input_tokens=10_000))  # $0.01
    finally:
        reset_current_thread_id(token)
    assert tel.cost_for_thread("m5-feature-a") == tel.total_cost
    assert tel.entries[0].thread_id == "m5-feature-a"


def test_concurrent_threads_get_isolated_cost() -> None:
    """The bug this fixes: two parallel meetings each see global cost,
    not their own cost. After the fix each thread's cost stays
    isolated even when the global counter accumulates both.
    """
    tel = Telemetry()

    tok_a = set_current_thread_id("m5-a")
    tel.record("tweedledee", TokenUsage(input_tokens=10_000))  # +$0.01 → A
    reset_current_thread_id(tok_a)

    tok_b = set_current_thread_id("m5-b")
    tel.record("tweedledum", TokenUsage(input_tokens=20_000))  # +$0.02 → B
    reset_current_thread_id(tok_b)

    tok_a2 = set_current_thread_id("m5-a")
    tel.record("alice", TokenUsage(input_tokens=10_000))  # +$0.01 → A
    reset_current_thread_id(tok_a2)

    # Each thread sees only its own spend, not the global $0.04.
    assert abs(tel.cost_for_thread("m5-a") - 0.02) < 1e-6
    assert abs(tel.cost_for_thread("m5-b") - 0.02) < 1e-6
    assert abs(tel.total_cost - 0.04) < 1e-6


def test_cost_for_thread_unknown_returns_zero() -> None:
    tel = Telemetry()
    tel.record("alice", TokenUsage(input_tokens=1000))
    assert tel.cost_for_thread("never-existed") == 0.0


def test_per_thread_cost_persisted_in_run_record(tmp_path: Path) -> None:
    """The run record carries per_thread_cost so post-hoc analysis
    can attribute spend back to specific iterations without re-
    summing entries by thread_id."""
    tel = Telemetry()
    tok = set_current_thread_id("contract-negotiation-feature-x")
    try:
        tel.record("tweedledee", TokenUsage(input_tokens=5000))
    finally:
        reset_current_thread_id(tok)
    path = tel.write_run_record(tmp_path, "test-pt")
    record = json.loads(path.read_text())
    assert "per_thread_cost" in record
    assert "contract-negotiation-feature-x" in record["per_thread_cost"]
    # Entries also stamped with thread_id for full traceability.
    assert record["entries"][0]["thread_id"] == "contract-negotiation-feature-x"
