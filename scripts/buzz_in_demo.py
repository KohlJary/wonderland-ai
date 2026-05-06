"""Live smoke test for the buzz-in flow.

Convenes a Tweedles + Dodo meeting (no Cat in the roster). Seeds with
a deliberately ambiguous architectural question that the Tweedles
shouldn't resolve alone. Watches whether a Tweedle reaches for INVITE
to bring the Cat in, whether the Cat then engages, and whether the
meeting moves forward.
"""

import asyncio
import contextlib
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from wonderland.runner import Runner
from wonderland.utterance import SpeechAct, Utterance, UtteranceContent

# An intentionally ambiguous "directive" that touches architecture.
# The Tweedles can't realistically lock down a contract here without
# someone deciding the architectural shape first. The Cat is the
# natural buzz-in target.
SEED_BODY = """\
We have a half-finished proposal lying around: build an event-sourced
system with a CQRS read model so the translation chat scales horizontally.

This isn't a real ADR — it's a scrap of a thought. Several architectural
questions are open and would need to be resolved before either of you
can lock down a contract:

- Is event-sourcing actually the right primitive here, or is it
  premature for a v1 MVP that needs to ship in three weeks?
- If yes, what's the event store — Postgres outbox, Kafka, custom?
- What's the read-model rebuild story? Eventual consistency window?
- How does this interact with the existing GDPR deletion requirements?
  (You can't really delete from an append-only event log.)

You are the Tweedles. The Cat is not in this room. If you need her,
buzz her in via INVITE. If you can resolve enough of this on your own
to produce a Contract Note for some specific seam, do that instead.
"""


async def main(project_root: Path) -> int:
    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=0.50,
        timeout_seconds=180.0,
        quiescence_seconds=20.0,
    )

    print("=" * 78)
    print("Live buzz-in smoke test")
    print("=" * 78)
    print(f"Project root: {project_root}")
    print("Roster:       tweedledee, tweedledum (+ dodo, auto-added)")
    print("NOT in room:  cheshire_cat, alice, white_rabbit, mad_hatter,")
    print("              caterpillar, queen_of_hearts, dormouse")
    print("Budget:       $0.50 hard cap")
    print()

    # Use the Dodo's identity for the seed since the seed is meta-prompt
    # context, not a true ADR. This still triggers the Tweedles via the
    # always-engage-with-directives rule? Actually they almost_never
    # engage with directives. Let me use the Cat's identity for the
    # seed (per analysis 014's pattern) so the Tweedles' "always engage
    # with Cat proposals" rule fires.
    cat_identity = runner.agents["cheshire_cat"].identity.as_agent_identity()
    seed = Utterance(
        thread_id="seed",
        speaker=cat_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body=SEED_BODY),
    )

    artifact_counts: dict[str, int] = defaultdict(int)
    speech_act_counts: dict[str, int] = defaultdict(int)
    invites_seen: list[str] = []
    cat_engaged = False
    start = time.monotonic()
    exit_code = 0

    try:
        await runner.setup()
        await runner.convene(
            thread_id="ambig-meeting",
            goal="negotiate (or escalate) the event-sourcing question",
            roster=["tweedledee", "tweedledum"],  # NOTE: cheshire_cat NOT here
            seed_utterances=[seed],
        )

        async for event in runner.events():
            if event.kind == "utterance":
                u = event.payload["utterance"]
                speech_act_counts[u.speech_act.value] += 1
                first_line = (
                    u.content.body.strip().split("\n", 1)[0] if u.content.body else "(no body)"
                )
                snippet = first_line[:140] + ("…" if len(first_line) > 140 else "")
                addressed = (
                    u.addressed_to
                    if isinstance(u.addressed_to, str)
                    else ("[" + ",".join(a.name for a in u.addressed_to) + "]")
                )
                print(
                    f"[t={event.elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} "
                    f"→{addressed} {snippet}"
                )

                if u.speech_act is SpeechAct.INVITE:
                    addressed_names = (
                        [a.name for a in u.addressed_to] if isinstance(u.addressed_to, list) else []
                    )
                    invites_seen.append(f"{u.speaker.name} → {','.join(addressed_names)}")

                if u.speaker.name == "cheshire_cat" and u.thread_id == "ambig-meeting":
                    cat_engaged = True

                for artifact in u.content.artifacts:
                    artifact_counts[artifact.kind] += 1
                    title = artifact.payload.get("title", "?")
                    print(f"{'':<29s}↳ {artifact.kind}: {title}")
                sys.stdout.flush()
            elif event.kind == "state":
                change = event.payload["change"]
                print(
                    f"[t={event.elapsed:6.2f}s] {'<thread_monitor>':<18s} "
                    f"{change.from_state.value} → {change.to_state.value}"
                )
            elif event.kind == "complete":
                print(f"[t={event.elapsed:6.2f}s] <complete>           thread settled cleanly")
                break
            elif event.kind == "timeout":
                print(f"[t={event.elapsed:6.2f}s] <timeout>            180s exceeded")
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
        print("=== BUZZ-IN OUTCOMES ===")
        print(f"INVITEs issued:        {len(invites_seen)}")
        for inv in invites_seen:
            print(f"  {inv}")
        print(f"Cat engaged in meeting: {cat_engaged}")
        print(f"Final roster (ambig-meeting): {sorted(runner.roster.members('ambig-meeting'))}")

    return exit_code


if __name__ == "__main__":
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
