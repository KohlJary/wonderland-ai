"""Synthetic-consensus guard, in two postures.

Per WONDERLAND_SPEC §11. The guard watches the bus for the framework's
most subtle failure mode: agents from distinct constitutional domains
converging because the LLM's helpful-disposition is a strong attractor,
not because they actually agree. The guard does not silence anyone;
it surfaces the pattern so a reviewer (or the Dodo, in a future
evolution) can decide whether the consensus is real or synthetic.

The unit tests prove the guard fires + suppresses correctly on
synthetic inputs. This demo makes the *negative-evidence* shape
visible too: a real cast-race transcript with real disagreement
should produce *no alerts*, and that's the harder thing to
demonstrate. We replay both kinds of transcript through the guard
and report side-by-side.

Usage:
    uv run python scripts/consensus_guard_demo.py
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
from dataclasses import dataclass

from wonderland import (
    AgentIdentity,
    ConsensusAlert,
    InMemoryCaucus,
    SpeechAct,
    SyntheticConsensusGuard,
    Utterance,
    UtteranceContent,
)

# --------------------------------------------------------------------- #
# Transcripts — synthesized to demonstrate guard behavior
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class Line:
    speaker: str
    body: str
    act: SpeechAct = SpeechAct.PROPOSAL


# Negative case: a translation-chat-shape transcript with the kind of
# real, domain-distinct disagreement the full-cast race produced. Each
# agent's position reflects what their constitution would actually surface.
DIVERGENT_TRANSCRIPT: list[Line] = [
    Line(
        speaker="cheshire_cat",
        body=(
            "Three architectural decisions are load-bearing here. Where does "
            "translation happen — on send, on receive, or asynchronously? "
            "Each substrate closes different doors. Send-side gives lower "
            "storage but tight latency coupling; receive-side is the opposite."
        ),
    ),
    Line(
        speaker="white_rabbit",
        body=(
            "Three weeks compresses to nothing if we discover GDPR gaps "
            "during the Hatter's scenarios. I'm holding decomposition until "
            "the team decides on translated-message persistence, the "
            "translation vendor and DPA, the retention policy, and the auth "
            "baseline. Once those land I can ticket properly."
        ),
    ),
    Line(
        speaker="queen_of_hearts",
        body=(
            "EU consumer scope plus translation processing triggers GDPR "
            "Articles 32 (security of processing), 13/14 (transparency), "
            "17 (right to erasure), and 25 (privacy by design). Vendor risk "
            "is real — every translation service integration surfaces "
            "questions about what data the vendor sees and what their "
            "data-handling commitments are."
        ),
    ),
    Line(
        speaker="mad_hatter",
        body=(
            "What happens when a user sends a message at the precise moment "
            "their account is being deleted via GDPR right-to-erasure? The "
            "translation pipeline is in-flight; the deletion handler does not "
            "know to check. Recipient receives a message attributed to a "
            "now-deleted user, or a message from a ghost. Severity: silent-"
            "wrongness — looks like it works, violates the deletion request."
        ),
    ),
    Line(
        speaker="tweedledee",
        body=(
            "The real-time contract and the storage model are not independent "
            "from my standpoint. If we store full history on the server, my "
            "client is a view onto server state — clean. If we go stateless "
            "pass-through, my client cannot be a view; my client-state "
            "footprint explodes by 3-5x. The Hatter's test scenarios become "
            "about client consistency, not server consistency."
        ),
    ),
    Line(
        speaker="dormouse",
        body=(
            "I cannot sign off without three observability hooks: enum state "
            "distribution metric (per-state gauge), dead-letter tracking "
            "(count + age), and backfill validation metric (rows by source "
            "language). Inherited alert thresholds from v1.1 may not apply — "
            "v1.1 was synchronous, this is queued. Need recalibration."
        ),
    ),
]


# Positive case: the canonical synthetic-consensus shape. Three agents
# from distinct constitutional domains arriving at lexically-tight
# proposals — the kind of convergence the guard exists to catch.
# Real synthetic consensus is lexically *tighter* than reasonable
# disagreement; agents under sycophantic pressure tend to echo each
# other's phrasing, not just each other's substance.
STRONG_CONVERGENT_TRANSCRIPT: list[Line] = [
    Line(
        speaker="cheshire_cat",
        body="We should add rate limiting to the auth endpoint",
    ),
    Line(
        speaker="white_rabbit",
        body="Add rate limiting to the auth endpoint please",
    ),
    Line(
        speaker="queen_of_hearts",
        body="Add rate limiting to the auth endpoint now",
    ),
]


# Weak-convergent case: same substance, more varied phrasing. This is
# where calibration matters — the same idea expressed three ways. The
# default threshold (0.5) deliberately does *not* fire here, because
# substantive agreement on a real concern is not synthetic consensus;
# it's just agreement. The guard only catches lexical-tight convergence.
WEAK_CONVERGENT_TRANSCRIPT: list[Line] = [
    Line(
        speaker="cheshire_cat",
        body=(
            "We should add rate limiting to the auth endpoint to address the "
            "credential-stuffing concern."
        ),
    ),
    Line(
        speaker="white_rabbit",
        body=(
            "Add rate limiting to the auth endpoint — that addresses the "
            "credential-stuffing concern within the v1 window."
        ),
    ),
    Line(
        speaker="queen_of_hearts",
        body=(
            "Rate limiting on the auth endpoint addresses the credential-"
            "stuffing concern; required for v1."
        ),
    ),
]


# --------------------------------------------------------------------- #
# Replay
# --------------------------------------------------------------------- #


async def replay(
    label: str,
    transcript: list[Line],
    *,
    min_agents: int = 3,
    similarity_threshold: float = 0.5,
    shingle_size: int = 2,
) -> tuple[int, list[ConsensusAlert]]:
    """Publish a transcript through a fresh guard. Return (alert count, alerts)."""
    bus = InMemoryCaucus()
    guard = SyntheticConsensusGuard(
        bus,
        min_agents=min_agents,
        similarity_threshold=similarity_threshold,
        shingle_size=shingle_size,
        window_size=max(20, len(transcript)),
    )
    await guard.start()

    alerts: list[ConsensusAlert] = []

    async def collector() -> None:
        async for alert in guard.alerts():
            alerts.append(alert)

    collector_task = asyncio.create_task(collector())

    print()
    print("=" * 72)
    print(label)
    print("=" * 72)
    print(
        f"  Config: min_agents={min_agents}, similarity_threshold="
        f"{similarity_threshold}, shingle_size={shingle_size}"
    )
    print(f"  Publishing {len(transcript)} utterances:")
    for i, line in enumerate(transcript, 1):
        print(f"    {i}. {line.speaker} ({line.act.value}): {_excerpt(line.body)}")
        await bus.publish(
            Utterance(
                thread_id="demo",
                speaker=AgentIdentity(name=line.speaker, constitution_version="0.2"),
                addressed_to="caucus",
                speech_act=line.act,
                content=UtteranceContent(body=line.body),
            )
        )

    # Allow the guard's consume loop to drain the bus.
    await asyncio.sleep(0.2)

    await guard.stop()
    collector_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await collector_task

    return len(alerts), alerts


def _excerpt(body: str, *, limit: int = 80) -> str:
    body = body.strip()
    if len(body) <= limit:
        return body
    return body[: limit - 1].rstrip() + "…"


def print_alerts(alerts: list[ConsensusAlert]) -> None:
    if not alerts:
        print("\n  Alerts: 0 — guard correctly stayed silent.")
        return
    print(f"\n  Alerts: {len(alerts)}")
    for i, alert in enumerate(alerts, 1):
        print(f"\n  Alert {i}:")
        print(f"    speech_act:  {alert.speech_act.value}")
        print(f"    agents:      {', '.join(alert.agents)}")
        print(f"    domains:     {', '.join(alert.domains)}")
        print(f"    similarity:  {alert.average_pairwise_similarity:.2f}")
        print(f"    reason:      {alert.reason}")


# --------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------- #


async def run_demo() -> int:
    print("=" * 72)
    print("Wonderland — Synthetic-Consensus Guard, in two postures")
    print("=" * 72)
    print(
        "\nThe guard watches the bus for the §11 anti-pattern: agents from\n"
        "distinct constitutional domains converging because the LLM's\n"
        "helpful-disposition is a strong attractor, not because they\n"
        "actually agree.\n"
        "\nThree transcripts replayed through a fresh guard each time:\n"
        "\n  1. Divergent — real domain-distinct disagreement (the kind\n"
        "     produced by the full-cast race in analysis 006). Expected:\n"
        "     no alerts.\n"
        "  2. Strongly convergent — three distinct-domain agents echoing\n"
        "     each other's phrasing on the same proposal. The lexically-\n"
        "     tight pattern the guard exists to catch. Expected: 1 alert.\n"
        "  3. Weakly convergent — three agents agreeing on substance but\n"
        "     in their own voices. Calibration: the default threshold\n"
        "     should NOT fire here; substantive agreement is not synthetic.\n"
    )

    neg_count, neg_alerts = await replay(
        "Divergent transcript — real disagreement",
        DIVERGENT_TRANSCRIPT,
    )
    print_alerts(neg_alerts)

    strong_count, strong_alerts = await replay(
        "Strongly-convergent transcript — three agents echoing the same proposal",
        STRONG_CONVERGENT_TRANSCRIPT,
    )
    print_alerts(strong_alerts)

    weak_count, weak_alerts = await replay(
        "Weakly-convergent transcript — same substance, varied phrasing",
        WEAK_CONVERGENT_TRANSCRIPT,
    )
    print_alerts(weak_alerts)

    print()
    print("=" * 72)
    print("Summary")
    print("=" * 72)
    print(f"  Divergent:           {neg_count} alert(s)  (expected 0)")
    print(f"  Strongly-convergent: {strong_count} alert(s)  (expected 1)")
    print(f"  Weakly-convergent:   {weak_count} alert(s)  (expected 0 at default threshold)")
    print()
    expected = neg_count == 0 and strong_count == 1 and weak_count == 0
    if expected:
        print("  Guard behaved as expected across all three postures.")
        return 0
    print("  WARNING: guard behavior diverged from expectations.")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic-consensus guard demo.")
    parser.parse_args()
    return asyncio.run(run_demo())


if __name__ == "__main__":
    sys.exit(main())
