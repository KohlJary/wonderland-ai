"""Tests for scripts/annotate_transcript.py — parser + renderer.

Acceptance from gameplan T39: run against an existing showcase
transcript and produce markdown containing all the structural
sections the manual analyses include. We exercise that on a small
synthetic transcript that mirrors the real-run shape.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the script as a module without requiring it to be on sys.path.
_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "annotate_transcript.py"
_spec = importlib.util.spec_from_file_location("annotate_transcript", _SCRIPT)
assert _spec is not None and _spec.loader is not None
annotate = importlib.util.module_from_spec(_spec)
sys.modules["annotate_transcript"] = annotate
_spec.loader.exec_module(annotate)


SYNTHETIC_LOG = """\
==============================================================================
T-test SHOWCASE
==============================================================================

──────────────────────────────────────────────────────────────────────────────
MEETING M1: produce stories + ADR
  thread_id: scoping
  roster:    ['alice', 'cheshire_cat', 'dodo']
──────────────────────────────────────────────────────────────────────────────
  M1[t=  0.00s] dodo               directive      →caucus Build a thing
  M1[t= 10.50s] alice              story          →caucus User can do X
  M1                             ↳ story: User can do X
  M1[t= 25.10s] cheshire_cat       proposal       →caucus Architecture proposal
  M1                             ↳ adr: Architecture
  M1[t= 30.00s] <thread_monitor> running → quiescent
  M1[t= 30.00s] dodo               acknowledgment →caucus Thread complete.
  M1[t= 30.00s] <thread_monitor> running → complete
  M1[t= 30.00s] <complete>

  ── M1 END ── outcome=COMPLETE
     elapsed:        30.0s
     this meeting:   5 calls, $0.0500
     running totals: 5 calls, $0.0500 / $1.00 cap
     artifacts:      2 (story×1, adr×1)

──────────────────────────────────────────────────────────────────────────────
MEETING M2: ship code
  thread_id: implementation
──────────────────────────────────────────────────────────────────────────────
  M2[t= 30.00s] dodo               directive      →caucus Implement
  M2[t= 45.00s] tweedledum         implementation →caucus Wrote backend
  M2                             ↳ implementation: Backend [side=backend]
[late-publish] tweedledee → thread 'scoping' (already COMPLETE) — suppressing concern: 'small extra observation'
[tweedledum] deliberate() raised TweedleResponseParseError: empty response — treating as silence
  M2[t= 60.00s] <thread_monitor> running → quiescent
  M2[t= 60.00s] <complete>

  ── M2 END ── outcome=COMPLETE
     elapsed:        30.0s
     this meeting:   3 calls, $0.0300
     running totals: 8 calls, $0.0800 / $1.00 cap
     artifacts:      1 (implementation×1)

==============================================================================
SUMMARY
==============================================================================
Total elapsed:  60.0s
Total cost:     $0.0800  (cap $1.00)
Total LLM calls: 8
"""


@pytest.fixture
def parsed(tmp_path: Path):
    log = tmp_path / "run.log"
    log.write_text(SYNTHETIC_LOG)
    return annotate.parse_run_log(log)


class TestParser:
    def test_extracts_headline_totals(self, parsed):
        assert parsed.total_elapsed == 60.0
        assert parsed.total_cost == 0.08
        assert parsed.total_calls == 8

    def test_extracts_meetings(self, parsed):
        assert len(parsed.meetings) == 2
        m1 = parsed.meetings[1]
        assert m1.title == "produce stories + ADR"
        assert m1.outcome == "COMPLETE"
        assert m1.elapsed_s == 30.0
        assert m1.calls == 5
        assert m1.cost == 0.05
        assert m1.artifacts == 2
        assert "story×1" in m1.artifact_breakdown

    def test_extracts_utterances(self, parsed):
        assert len(parsed.utterances) >= 5
        speakers = {u.speaker for u in parsed.utterances}
        assert {"dodo", "alice", "cheshire_cat", "tweedledum"}.issubset(speakers)
        speech_acts = {u.speech_act for u in parsed.utterances}
        assert {"story", "proposal", "implementation"}.issubset(speech_acts)

    def test_extracts_state_transitions(self, parsed):
        kinds = {(t.from_state, t.to_state) for t in parsed.transitions}
        assert ("running", "quiescent") in kinds
        assert ("running", "complete") in kinds

    def test_extracts_late_publishes(self, parsed):
        assert len(parsed.late_publishes) == 1
        lp = parsed.late_publishes[0]
        assert lp.speaker == "tweedledee"
        assert lp.thread == "scoping"
        assert lp.speech_act == "concern"

    def test_extracts_parse_errors(self, parsed):
        assert len(parsed.parse_errors) == 1
        pe = parsed.parse_errors[0]
        assert pe.speaker == "tweedledum"
        assert pe.error_type == "TweedleResponseParseError"


class TestRenderer:
    def test_produces_required_sections(self, parsed):
        md = annotate.render(parsed, telemetry={}, artifact_counts={}, diffstat=None)
        # Acceptance: all structural sections from the gameplan spec
        for section in (
            "# Analysis stub",
            "## Headline numbers",
            "## Per-meeting breakdown",
            "## Speech-act distribution",
            "## Per-agent breakdown",
            "## Thread-state log",
            "## Late-publish catalog",
            "## Parse-error catalog",
            "## Auto-detected patterns",
            "## Interpretation (fill in)",
        ):
            assert section in md, f"missing section: {section}"

    def test_includes_diffstat_when_provided(self, parsed):
        md = annotate.render(
            parsed,
            telemetry={},
            artifact_counts={},
            diffstat=" file.py | 10 ++++++----\n 1 file changed, 6 insertions(+)",
        )
        assert "## Code shipped" in md
        assert "file.py" in md

    def test_omits_diffstat_when_absent(self, parsed):
        md = annotate.render(parsed, telemetry={}, artifact_counts={}, diffstat=None)
        assert "## Code shipped" not in md

    def test_includes_artifact_counts(self, parsed):
        md = annotate.render(
            parsed,
            telemetry={},
            artifact_counts={"stories": 5, "tickets": 7},
            diffstat=None,
        )
        assert "## Artifacts persisted" in md
        assert "stories/" in md and "tickets/" in md


class TestPatternDetection:
    def test_late_publish_signature_fires(self, parsed):
        findings = annotate.detect_patterns(parsed, telemetry={})
        assert any("Late-publish" in f for f in findings)

    def test_parse_error_signature_fires(self, parsed):
        findings = annotate.detect_patterns(parsed, telemetry={})
        assert any("Parse-error" in f for f in findings)

    def test_cat_cache_miss_signature_fires(self, parsed):
        bad_cat_telemetry = {
            "per_agent": {
                "cheshire_cat": {
                    "input_tokens": 50000,
                    "cache_creation_input_tokens": 20000,
                    "cache_read_input_tokens": 5000,  # 5000 / 75000 ~= 7%
                }
            }
        }
        findings = annotate.detect_patterns(parsed, telemetry=bad_cat_telemetry)
        assert any("Cat-cache-miss" in f for f in findings)

    def test_cat_cache_miss_signature_silent_when_healthy(self, parsed):
        good_cat_telemetry = {
            "per_agent": {
                "cheshire_cat": {
                    "input_tokens": 5000,
                    "cache_creation_input_tokens": 10000,
                    "cache_read_input_tokens": 100000,  # heavy reuse
                }
            }
        }
        findings = annotate.detect_patterns(parsed, telemetry=good_cat_telemetry)
        assert not any("Cat-cache-miss" in f for f in findings)
