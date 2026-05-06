"""Live test: Tweedles use the tool surface to ship actual code.

Builds on analysis 014's ADR-001 + the agreed contract notes from the
prior follow-on test. Convenes a Tweedle-Cat-Dodo meeting with those
artifacts as opening context, asks the Tweedles to ship a minimal
backend handler stub for the message-translation endpoint. Verifies
that files actually land on disk in the project sandbox.
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
"""

ADR_001_ARTIFACT = Artifact(
    kind="adr",
    payload={
        "number": 1,
        "slug": "third-party-translation-service-with-synchronous-on-read-model",
        "title": "Third-Party Translation Service with Synchronous On-Read Model",
        "decision": (
            "Integrate third-party translation service. Persist original "
            "messages only; translate on read, not on write. Deliver via "
            "WebSocket with visible translation-status signals. Timeout "
            "and graceful degradation to original message if translation "
            "exceeds SLA (2 seconds)."
        ),
        "tradeoffs": [
            "Closes: in-house training, offline-first translation, stateless HTTP backend.",
            "Opens: predictable translation cost, third-party SLA liability, simpler GDPR deletion.",
        ],
        "status": "Proposed",
    },
)

# Synthesize the agreed contract notes from analysis 014's run as a
# Cat-spoken summary the Tweedles can compose against. (Real flow: the
# convene mechanism would scoop these from the prior meeting's
# contract-notes/ registry; for this test we just hand them in.)
CONTRACTS_BODY = """\
Three contracts agreed in the prior contract-negotiation meeting:

1. **Translation Status Signal Shape (v1)**: Each message has a
   translation_status field with enum values
   {pending, translated, failed, timeout}. The status is updated
   on the server and pushed to clients via the message-translated
   WebSocket event.

2. **Translation SLA Fallback Behavior (v1)**: Backend emits
   translation_failed event with failure_reason enum
   {timeout, service_error, network_error}. After 2-second SLA the
   server returns the original message with translation_status=timeout.

3. **WebSocket Statefulness (v1)**: Backend translation service is
   stateless. Each request includes message_id, source_language,
   target_language. Frontend manages client-side cache lifecycle.

The directive for this meeting: ship a minimal Python backend handler
for the message-translation endpoint that honors these contracts.
Specifically:
- One file: `src/translation_handler.py`
- One async function: `handle_translation_request(message_id,
  source_lang, target_lang)` returning a dict matching the contract
  envelope.
- Stub the actual translator call (no real network) — return
  {"status": "translated", "translated_text": "[stub]"} after a
  notional 50ms delay.
- Handle the timeout case: if translator takes >2s, return
  {"status": "timeout", "translated_text": null}.
- Handle service errors: return {"status": "failed",
  "failure_reason": "service_error"}.

Tweedledum drives the implementation; Tweedledee can suggest if the
shape needs revision. Ship the file via write_file. Use list_files
and read_file to check what's already in src/ first.
"""


async def main(project_root: Path) -> int:
    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=1.5,
        timeout_seconds=240.0,
        quiescence_seconds=30.0,
    )

    print("=" * 78)
    print("Live tool-use test: Tweedles ship a translation handler")
    print("=" * 78)
    print(f"Project root: {project_root}")
    print("Roster:       tweedledee, tweedledum, cheshire_cat (+ dodo)")
    print("Budget:       $1.50 hard cap")
    print()

    cat_identity = runner.agents["cheshire_cat"].identity.as_agent_identity()
    seed_adr = Utterance(
        thread_id="seed",
        speaker=cat_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body=ADR_001_BODY, artifacts=[ADR_001_ARTIFACT]),
    )
    seed_contracts = Utterance(
        thread_id="seed",
        speaker=cat_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.PROPOSAL,
        content=UtteranceContent(body=CONTRACTS_BODY),
    )

    artifact_counts: dict[str, int] = defaultdict(int)
    speech_act_counts: dict[str, int] = defaultdict(int)
    start = time.monotonic()
    exit_code = 0

    try:
        await runner.setup()
        await runner.convene(
            thread_id="ship-handler",
            goal="ship src/translation_handler.py honoring contract v1",
            roster=["tweedledee", "tweedledum", "cheshire_cat"],
            seed_utterances=[seed_adr, seed_contracts],
        )

        async for event in runner.events():
            if event.kind == "utterance":
                u = event.payload["utterance"]
                speech_act_counts[u.speech_act.value] += 1
                first_line = (
                    u.content.body.strip().split("\n", 1)[0] if u.content.body else "(no body)"
                )
                snippet = first_line[:140] + ("…" if len(first_line) > 140 else "")
                print(
                    f"[t={event.elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} {snippet}"
                )
                for artifact in u.content.artifacts:
                    artifact_counts[artifact.kind] += 1
                    title = artifact.payload.get("title", "?")
                    files = (
                        artifact.payload.get("files_touched") or artifact.payload.get("files") or []
                    )
                    files_s = f" files={files}" if files else ""
                    print(f"{'':<29s}↳ {artifact.kind}: {title}{files_s}")
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
        print("Files in project_root/src/ (the actual code shipped):")
        src = project_root / "src"
        if src.is_dir():
            for f in sorted(src.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(project_root)
                    print(f"  {rel} ({f.stat().st_size} bytes)")
        else:
            print("  (no src/ — nothing shipped to disk)")

    return exit_code


if __name__ == "__main__":
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
