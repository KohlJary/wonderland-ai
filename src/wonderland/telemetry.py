"""Token telemetry — per-run cost tracking using actual Haiku 4.5 pricing.

Per WONDERLAND_SPEC §11 token-telemetry mitigation, and per the T34
restructure after the $8 polite-deadlock surprise: every multi-agent
run produces a structured per-run record under
``<project_root>/.wonderland/telemetry/run-NNN.json`` capturing per-
call usage by agent, the running cost, and the budget headroom.

Pricing constants are sourced from the live Anthropic docs (see
the reference_haiku_pricing memory). They live as module-level
constants here so a future model upgrade is a one-line change. The
formula handles the four cost components the API reports —
uncached input, cache writes (5-minute), cache reads, and output —
so the cost number matches what the dashboard actually charges.
"""

from __future__ import annotations

import contextvars
import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from wonderland.llm import TokenUsage

# --------------------------------------------------------------------- #
# Per-thread cost attribution (parallel meeting fix)
# --------------------------------------------------------------------- #
#
# Parallel meetings (T93) broke cost attribution: meeting_budget /
# cost_delta both used ``runner.total_cost - cost_before``, which is
# the *global* accumulator. With N concurrent iterations all reading
# the global, each iteration sees the sum of all sibling spend and
# trips per-meeting budget caps prematurely (8/9 M5 iterations
# aborted on rotation 0 in the May 10 run that motivated this fix).
#
# The agent's `speak()` loop sets the current thread_id at the top of
# each turn; `record()` reads it and stamps each entry with the
# attributing thread. ``cost_for_thread()`` then gives meetings a way
# to budget-check just their own iteration's spend.
#
# ContextVar (not explicit kwarg) so the LLMClient signature stays
# clean — call attribution is an orthogonal cross-cutting concern,
# not part of the LLM API.
_current_thread_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "wonderland_telemetry_thread_id", default=""
)


def set_current_thread_id(thread_id: str) -> contextvars.Token:
    """Stamp subsequent `Telemetry.record()` calls with this thread_id.

    Call at the top of an agent turn; reset in a `finally` via the
    returned Token so context unwinds cleanly even on cancellation.
    """
    return _current_thread_id.set(thread_id)


def reset_current_thread_id(token: contextvars.Token) -> None:
    _current_thread_id.reset(token)


def get_current_thread_id() -> str:
    return _current_thread_id.get()

# --------------------------------------------------------------------- #
# Pricing — Claude Haiku 4.5 per-MTok rates (USD)
# --------------------------------------------------------------------- #


HAIKU_4_5_INPUT_PER_MTOK = 1.00
HAIKU_4_5_OUTPUT_PER_MTOK = 5.00
HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK = 1.25
HAIKU_4_5_CACHE_READ_PER_MTOK = 0.10


def estimate_cost(usage: TokenUsage) -> float:
    """Compute the dollar cost of one TokenUsage record at Haiku 4.5 prices.

    The formula matches what the Anthropic dashboard charges:
    uncached input tokens at the base rate, cache writes at the
    5-minute cache rate (1.25x base), cache reads at 0.10x base, and
    output tokens at the output rate.
    """
    return (
        usage.input_tokens * HAIKU_4_5_INPUT_PER_MTOK / 1_000_000
        + usage.cache_creation_input_tokens * HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK / 1_000_000
        + usage.cache_read_input_tokens * HAIKU_4_5_CACHE_READ_PER_MTOK / 1_000_000
        + usage.output_tokens * HAIKU_4_5_OUTPUT_PER_MTOK / 1_000_000
    )


# --------------------------------------------------------------------- #
# Telemetry aggregator
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class TelemetryEntry:
    """One LLM call's worth of usage, with the agent + cost attribution.

    ``thread_id`` carries the meeting/iteration the call happened
    inside, captured from the contextvar at record time. Empty when
    no thread context was set (e.g. a setup call outside any
    meeting). Used by ``cost_for_thread()`` for per-meeting budgeting.
    """

    agent: str
    usage: TokenUsage
    cost: float
    timestamp: datetime
    thread_id: str = ""


@dataclass
class Telemetry:
    """In-process aggregator for a Runner's per-call token usage.

    Each agent's ``LLMClient`` callback is wired to ``record_for(name)``
    so usage gets attributed to the right agent. Total cost updates
    incrementally so a budget-cap loop can poll cheaply.

    Per-thread cost is also tracked incrementally (``_per_thread_cost``)
    so per-meeting budget checks can poll their own iteration's spend
    in O(1) — critical for parallel meetings where the global counter
    is shared across siblings.

    At end-of-run, ``write_run_record(project_root, run_id)`` writes a
    structured JSON file under ``<project_root>/.wonderland/telemetry/``
    that subsequent analyses can cite without re-deriving from raw
    transcripts.
    """

    entries: list[TelemetryEntry] = field(default_factory=list)
    _total_cost: float = 0.0
    _per_thread_cost: dict[str, float] = field(default_factory=dict)

    def record_for(self, agent: str):
        """Return a callback that, when invoked with TokenUsage, records it.

        Plug into ``LLMClient(on_token_usage=tel.record_for("alice"))``.
        """

        def _callback(usage: TokenUsage) -> None:
            self.record(agent, usage)

        return _callback

    def record(self, agent: str, usage: TokenUsage) -> TelemetryEntry:
        cost = estimate_cost(usage)
        thread_id = _current_thread_id.get()
        entry = TelemetryEntry(
            agent=agent,
            usage=usage,
            cost=cost,
            timestamp=datetime.now(UTC),
            thread_id=thread_id,
        )
        self.entries.append(entry)
        self._total_cost += cost
        if thread_id:
            self._per_thread_cost[thread_id] = (
                self._per_thread_cost.get(thread_id, 0.0) + cost
            )
        return entry

    @property
    def total_cost(self) -> float:
        return self._total_cost

    @property
    def call_count(self) -> int:
        return len(self.entries)

    def cost_for_thread(self, thread_id: str) -> float:
        """Return cumulative cost attributed to ``thread_id``.

        Returns 0.0 for an unknown thread_id. O(1) — backed by an
        incrementally-updated dict, not a scan over entries.
        """
        return self._per_thread_cost.get(thread_id, 0.0)

    def per_agent_summary(self) -> dict[str, dict[str, int | float]]:
        """Aggregate by agent: calls / input / output / cache_w / cache_r / cost."""
        per_agent: dict[str, dict[str, int | float]] = defaultdict(
            lambda: {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 0,
                "cost": 0.0,
            }
        )
        for entry in self.entries:
            row = per_agent[entry.agent]
            row["calls"] = int(row["calls"]) + 1
            row["input_tokens"] = int(row["input_tokens"]) + entry.usage.input_tokens
            row["output_tokens"] = int(row["output_tokens"]) + entry.usage.output_tokens
            row["cache_creation_input_tokens"] = (
                int(row["cache_creation_input_tokens"]) + entry.usage.cache_creation_input_tokens
            )
            row["cache_read_input_tokens"] = (
                int(row["cache_read_input_tokens"]) + entry.usage.cache_read_input_tokens
            )
            row["cost"] = float(row["cost"]) + entry.cost
        return dict(per_agent)

    def write_run_record(
        self, project_root: Path, run_id: str, *, extra: dict | None = None
    ) -> Path:
        """Persist the per-run telemetry as JSON and return the path.

        The structured shape lets analysis scripts (T39) read cost data
        without parsing prose. ``extra`` carries run-level metadata the
        Runner adds (directive, scenario, outcome, elapsed, etc).
        """
        directory = project_root / ".wonderland" / "telemetry"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"run-{run_id}.json"
        record = {
            "run_id": run_id,
            "model": "claude-haiku-4-5-20251001",
            "pricing_per_mtok": {
                "input": HAIKU_4_5_INPUT_PER_MTOK,
                "output": HAIKU_4_5_OUTPUT_PER_MTOK,
                "cache_write_5m": HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK,
                "cache_read": HAIKU_4_5_CACHE_READ_PER_MTOK,
            },
            "total_cost": round(self._total_cost, 6),
            "total_calls": self.call_count,
            "per_agent": self.per_agent_summary(),
            "per_thread_cost": {
                tid: round(cost, 6)
                for tid, cost in self._per_thread_cost.items()
            },
            "entries": [
                {
                    "agent": e.agent,
                    "thread_id": e.thread_id,
                    "input_tokens": e.usage.input_tokens,
                    "output_tokens": e.usage.output_tokens,
                    "cache_creation_input_tokens": e.usage.cache_creation_input_tokens,
                    "cache_read_input_tokens": e.usage.cache_read_input_tokens,
                    "cost": round(e.cost, 6),
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.entries
            ],
            **(extra or {}),
        }
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return path


__all__ = [
    "HAIKU_4_5_CACHE_READ_PER_MTOK",
    "HAIKU_4_5_CACHE_WRITE_5M_PER_MTOK",
    "HAIKU_4_5_INPUT_PER_MTOK",
    "HAIKU_4_5_OUTPUT_PER_MTOK",
    "Telemetry",
    "TelemetryEntry",
    "estimate_cost",
]
