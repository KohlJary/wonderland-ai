"""Cross-meeting composition demo: ADR-001 (from a prior meeting) drives
contract negotiation in a Tweedle-Cat-Dodo follow-up meeting.

Originally hand-built (analysis 014) before Runner.convene existed; now
uses the proper Block 2b convene mechanism. The demo constructs the
prior meeting's ADR-001 as a Cat-spoken proposal utterance, then
convenes a follow-up meeting with the Tweedles as the rostered
participants and the proposal as the opening seed. The Tweedles'
engagement rules `always(SpeechAct.PROPOSAL, condition=speaker_is("cheshire_cat"))`
fire on the seed; negotiation proceeds.

The Cat's ADR-001 is hardcoded here for reproducibility — in a real
follow-up meeting the convenor would scoop the artifact from the
prior thread's episodic memory or the artifact registry.
"""

import asyncio
import contextlib
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from wonderland.runner import Runner
from wonderland.utterance import Artifact, SpeechAct, Utterance, UtteranceContent

ADR_001_BODY = """\
The architecture for the translation chat MVP. Three forces in tension:
near-real-time UX, third-party translation cost predictability, and
GDPR compliance under EU consumer scope. Persisting both originals and
translations doubles the deletion surface and creates a translation
cache that ages poorly. Persisting originals only and translating
on read keeps the GDPR surface minimal but couples display latency
to translator SLA. The decision routes the latency tradeoff to a
2-second SLA with graceful degradation.

Two open questions are explicitly routed to the Tweedles for the next
round: WebSocket state management strategy (sticky sessions vs shared
cache) and the seam shape between frontend and backend for the
translation status signals. Both touch the contract surface that the
pair owns.
"""

ADR_001_ARTIFACT = Artifact(
    kind="adr",
    payload={
        "number": 1,
        "slug": "third-party-translation-service-with-synchronous-on-read-model",
        "title": "Third-Party Translation Service with Synchronous On-Read Model",
        "context": (
            "Three-week MVP for real-time chat with message translation. Two "
            "language pairs at launch. GDPR scope requires explicit data-flow "
            "boundaries and processor agreements. Real-time UX requires low "
            "latency and visible status signals."
        ),
        "decision": (
            "Integrate third-party translation service (vendor TBD, pending "
            "Queen's processor-agreement review). Persist original messages "
            "only; translate on read, not on write. Deliver via WebSocket "
            "with visible translation-status signals. Timeout and graceful "
            "degradation to original message if translation exceeds SLA "
            "(propose: 2 seconds)."
        ),
        "tradeoffs": [
            "Closes: custom model tuning, in-house training, offline-first translation, truly stateless HTTP backend.",
            "Opens: predictable translation cost, third-party SLA liability, simpler GDPR deletion (single data copy).",
            "Requires decision: which third-party translator (Queen review).",
            "Requires decision: WebSocket state management strategy (Tweedles to propose).",
            "Uncertain: whether 2-second translation timeout is acceptable to users.",
        ],
        "status": "Proposed",
    },
)


async def main(project_root: Path) -> int:
    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=1.0,
        timeout_seconds=240.0,
        quiescence_seconds=30.0,
    )

    print("=" * 78)
    print("Cross-meeting composition demo: prior ADR drives contract negotiation")
    print("=" * 78)
    print(f"Project root: {project_root}")
    print("Roster:       tweedledee, tweedledum, cheshire_cat (+ dodo)")
    print("Goal:         produce Contract Note for WebSocket state management")
    print("Budget:       $1.00 hard cap")
    print()
    print("--- Dance ---")

    artifact_counts: dict[str, int] = defaultdict(int)
    speech_act_counts: dict[str, int] = defaultdict(int)
    start = time.monotonic()
    exit_code = 0

    try:
        await runner.setup()

        # Block 2b: convene the follow-up meeting with the prior meeting's
        # Cat-spoken ADR-001 proposal as opening context. The convene
        # mechanism registers the roster (Dodo auto-added), re-stamps the
        # seed's thread_id to the new meeting, and publishes it. The
        # Tweedles' engagement rule on Cat proposals fires; negotiation
        # proceeds without any further wiring.
        cat_identity = runner.agents["cheshire_cat"].identity.as_agent_identity()
        adr_proposal_seed = Utterance(
            thread_id="prior-scoping-meeting",  # convene re-stamps to "main"
            speaker=cat_identity,
            addressed_to="caucus",
            speech_act=SpeechAct.PROPOSAL,
            content=UtteranceContent(body=ADR_001_BODY, artifacts=[ADR_001_ARTIFACT]),
        )
        await runner.convene(
            thread_id="main",
            goal="produce Contract Note for WebSocket state management",
            roster=["tweedledee", "tweedledum", "cheshire_cat"],
            seed_utterances=[adr_proposal_seed],
        )

        async for event in runner.events():
            if event.kind == "utterance":
                u = event.payload["utterance"]
                speech_act_counts[u.speech_act.value] += 1
                first_line = u.content.body.strip().split("\n", 1)[0]
                snippet = first_line[:140] + ("…" if len(first_line) > 140 else "")
                print(
                    f"[t={event.elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} {snippet}"
                )
                for artifact in u.content.artifacts:
                    artifact_counts[artifact.kind] += 1
                    title = artifact.payload.get("title", "?")
                    extra = []
                    for key in ("operation", "state", "side"):
                        v = artifact.payload.get(key)
                        if v:
                            extra.append(f"{key}={v}")
                    extra_s = f" [{', '.join(extra)}]" if extra else ""
                    print(f"{'':<29s}↳ {artifact.kind}: {title}{extra_s}")
                sys.stdout.flush()
            elif event.kind == "state":
                change = event.payload["change"]
                print(
                    f"[t={event.elapsed:6.2f}s] {'<thread_monitor>':<18s} "
                    f"{change.from_state.value} → {change.to_state.value} ({change.reason})"
                )
            elif event.kind == "complete":
                print(f"[t={event.elapsed:6.2f}s] <complete>           thread settled cleanly")
                break
            elif event.kind == "timeout":
                print(f"[t={event.elapsed:6.2f}s] <timeout>            240s exceeded")
                exit_code = 1
                break
            elif event.kind == "budget_exceeded":
                cost = event.payload["cost"]
                print(f"[t={event.elapsed:6.2f}s] <budget>             EXCEEDED ${cost:.2f}")
    finally:
        elapsed_total = time.monotonic() - start
        await runner.teardown()
        print()
        print("--- Summary ---")
        print(f"Elapsed:        {elapsed_total:.1f}s")
        print(f"Total cost:     ${runner.total_cost:.4f}")
        print(f"LLM calls:      {runner.telemetry.call_count}")
        print()
        print("Speech acts:")
        for act, count in sorted(speech_act_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {act:18s} {count}")
        print()
        print("Artifacts on disk:")
        for kind, count in sorted(artifact_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {kind:18s} {count}")
        print()
        print("Per-agent token usage:")
        for agent, row in sorted(
            runner.telemetry.per_agent_summary().items(),
            key=lambda kv: -float(kv[1]["cost"]),
        ):
            print(
                f"  {agent:18s} calls={int(row['calls']):3d} "
                f"in={int(row['input_tokens']):7d} "
                f"out={int(row['output_tokens']):6d} "
                f"cost=${float(row['cost']):.4f}"
            )

    return exit_code


if __name__ == "__main__":
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
