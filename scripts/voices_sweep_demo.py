"""Voices sweep — six new P5 agents, each speaking in isolation on the same root scenario.

Where ``alice_demo.py`` runs Alice solo to see her voice, this runs all
six P5 agents back-to-back and prints them side-by-side. Each agent
gets the trigger shape its §III engagement rules actually accept (a
directive for Hatter and Queen; a synthesized implementation for
Caterpillar and Dormouse; a synthesized ticket for the Tweedles), but
all six triggers are rooted in the same translation-chat scenario so
the comparison stays meaningful.

The point is to see — in one transcript — whether identity actually
produces six distinct voices on equivalent input. Six paragraphs
that all sound like "a helpful AI assistant" would be falsification
of the project's central claim. Six paragraphs that each sound like
themselves is what the thesis predicts.

Usage:
    uv run python scripts/voices_sweep_demo.py
    uv run python scripts/voices_sweep_demo.py --project-root ./voices-output
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from wonderland import (
    AgentIdentity,
    AgentMemory,
    Caterpillar,
    Dormouse,
    ImplementationRegistry,
    InMemoryCaucus,
    LLMClient,
    MadHatter,
    ObservationRegistry,
    QueenOfHearts,
    ReviewRegistry,
    RulingRegistry,
    SpeechAct,
    TestScenarioRegistry,
    TokenUsage,
    Tweedledee,
    Tweedledum,
    Utterance,
    UtteranceContent,
    WonderlandAgent,
)

# --------------------------------------------------------------------- #
# The root scenario — every per-agent trigger derives from this
# --------------------------------------------------------------------- #


ROOT_DIRECTIVE = (
    "Build a translation-integrated chat application. Initial scope: "
    "two users in different language groups exchanging short messages "
    "with near-real-time translation. EU consumer scope (GDPR applies). "
    "Targeting a v1 launch in three weeks."
)


SYNTHESIZED_FRONTEND_IMPL = """\
Implementation: TranslationMessageList component (frontend).

Wired the message list to the new translation WebSocket subscription using a
virtual scroll for history. Added a client-side pending-translation queue
keyed by message_id (TTL 60s; entries TTL into an error-recoverable surface
if no translation arrives).

UI states implemented: loading (skeleton bubbles), empty ('no messages yet'
tip), error-recoverable ('reconnecting...' with retry), stale (warning
badge when the subscription is older than 30s). Offline composition not
yet supported.

Files:
- src/chat/MessageList.tsx: subscription wiring + virtual scroll
- src/chat/usePendingTranslations.ts: client-side queue hook + TTL logic

Contract: message-envelope v3 (translation_status enum + source_lang FK).
Open questions for tweedledum: does message-translated arrive once per
language, or once per message? Ready for review.

```typescript
function MessageList({ thread_id }: Props) {
  const messages = useWebSocketSubscription(thread_id);
  const pending = usePendingTranslations(messages);
  return <VirtualScroll items={pending.merged} />;
}
```
"""


SYNTHESIZED_BACKEND_IMPL = """\
Implementation: translation worker pipeline (backend).

Deployed translation-service v1.2 to prod-eu-west-1 at 14:00 UTC. Worker
pool picks up jobs and persists results with a translation_status enum
(pending → translating → ready | failed); WebSocket emits
message-translated on completion or message-translation-failed on
dead-letter.

Standard observability hooks wired: request_count, error_rate,
latency_p50/p95/p99, queue_depth. Logs go to centralized stack with
structured fields (app, level, request_id, span_id). Dashboard at
https://grafana.internal/d/translation/overview. Alert thresholds
inherited from translation-service v1.1.

Invariants enforced:
- every translated message has exactly one source_lang (DB FK NOT NULL)
- translation_status transitions are monotonic (DB CHECK constraint)

Schema changes: migration 0042 adds translation_status enum + source_lang
FK to messages. Backward-compatible: existing rows backfilled with
status='not_required' and source_lang derived from sender locale.

Looking for post-deploy sign-off.
"""


SYNTHESIZED_FRONTEND_TICKET = """\
Ticket-014: Wire the translation message list to the new WebSocket subscription.

Owner: tweedledee. Tier: v1. Estimate: 1 day, 80% confident.

Acceptance:
- Messages render in conversation order, oldest at top.
- Loading skeleton on first paint until subscription connects.
- Error-recoverable state on WebSocket disconnect with manual retry.
- 'Stale' badge appears when subscription is older than 30 seconds.
- Pending-translation states render distinctly from ready translations.

Contract: message-envelope v3 (translation_status enum + source_lang FK);
message-translated WebSocket event.
"""


SYNTHESIZED_BACKEND_TICKET = """\
Ticket-015: Implement translation worker pipeline.

Owner: tweedledum. Tier: v1. Estimate: 2 days, 70% confident.

Acceptance:
- Translation jobs picked up from queue and persisted with translation_status
  enum (pending → translating → ready | failed).
- message-translated event emitted on completion.
- message-translation-failed event emitted on dead-letter.
- Failure modes handled: worker crash mid-message (job re-enqueued), DB
  write succeeds but WebSocket emit fails (outbox table + retry).

Invariants required:
- Every translated message has exactly one source_lang.
- translation_status transitions are monotonic.

Contract: message-envelope v3 (matches frontend ticket-014).
"""


# --------------------------------------------------------------------- #
# Per-agent run configuration
# --------------------------------------------------------------------- #


@dataclass(frozen=True)
class AgentRun:
    """Everything needed to run one agent in isolation against one trigger."""

    name: str
    factory: Callable[[AgentMemory, InMemoryCaucus, LLMClient, Path], WonderlandAgent]
    primer_speaker: str
    primer_act: SpeechAct
    primer_body: str
    trigger_summary: str
    """One-line description of what trigger this agent receives — for the report header."""


def _hatter(memory, bus, llm, root):
    return MadHatter(
        memory=memory, bus=bus, llm=llm, test_scenario_registry=TestScenarioRegistry(root)
    )


def _caterpillar(memory, bus, llm, root):
    return Caterpillar(memory=memory, bus=bus, llm=llm, review_registry=ReviewRegistry(root))


def _queen(memory, bus, llm, root):
    return QueenOfHearts(memory=memory, bus=bus, llm=llm, ruling_registry=RulingRegistry(root))


def _dormouse(memory, bus, llm, root):
    return Dormouse(memory=memory, bus=bus, llm=llm, observation_registry=ObservationRegistry(root))


def _dee(memory, bus, llm, root):
    return Tweedledee(
        memory=memory, bus=bus, llm=llm, implementation_registry=ImplementationRegistry(root)
    )


def _dum(memory, bus, llm, root):
    return Tweedledum(
        memory=memory, bus=bus, llm=llm, implementation_registry=ImplementationRegistry(root)
    )


SWEEP: list[AgentRun] = [
    AgentRun(
        name="mad_hatter",
        factory=_hatter,
        primer_speaker="dodo",
        primer_act=SpeechAct.DIRECTIVE,
        primer_body=ROOT_DIRECTIVE,
        trigger_summary="Dodo directive (Hatter §III: ALWAYS engages with directive)",
    ),
    AgentRun(
        name="queen_of_hearts",
        factory=_queen,
        primer_speaker="dodo",
        primer_act=SpeechAct.DIRECTIVE,
        primer_body=ROOT_DIRECTIVE,
        trigger_summary="Dodo directive (Queen §III: SELECTIVELY for compliance keywords; GDPR keyword present)",
    ),
    AgentRun(
        name="caterpillar",
        factory=_caterpillar,
        primer_speaker="tweedledee",
        primer_act=SpeechAct.IMPLEMENTATION,
        primer_body=SYNTHESIZED_FRONTEND_IMPL,
        trigger_summary="Synthesized Tweedledee implementation (Caterpillar §III: ALWAYS engages)",
    ),
    AgentRun(
        name="dormouse",
        factory=_dormouse,
        primer_speaker="tweedledum",
        primer_act=SpeechAct.IMPLEMENTATION,
        primer_body=SYNTHESIZED_BACKEND_IMPL,
        trigger_summary="Synthesized Tweedledum prod deploy (Dormouse §III: ALWAYS for tweedle implementation)",
    ),
    AgentRun(
        name="tweedledee",
        factory=_dee,
        primer_speaker="white_rabbit",
        primer_act=SpeechAct.TICKET,
        primer_body=SYNTHESIZED_FRONTEND_TICKET,
        trigger_summary="Synthesized Rabbit ticket (Tweedledee §III: ALWAYS for tickets)",
    ),
    AgentRun(
        name="tweedledum",
        factory=_dum,
        primer_speaker="white_rabbit",
        primer_act=SpeechAct.TICKET,
        primer_body=SYNTHESIZED_BACKEND_TICKET,
        trigger_summary="Synthesized Rabbit ticket (Tweedledum §III: ALWAYS for tickets)",
    ),
]


# --------------------------------------------------------------------- #
# Per-agent execution
# --------------------------------------------------------------------- #


@dataclass
class RunResult:
    name: str
    response: Utterance | None
    elapsed: float
    usage: list[TokenUsage] = field(default_factory=list)
    timed_out: bool = False


async def run_one_agent(agent_run: AgentRun, project_root: Path, *, timeout: float) -> RunResult:
    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(project_root, agent_run.name)
    await memory.open()

    usage_log: list[TokenUsage] = []
    llm = LLMClient(on_token_usage=usage_log.append)

    agent = agent_run.factory(memory, bus, llm, project_root)
    observer = bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(agent.run())

    primer = Utterance(
        thread_id=f"sweep-{agent_run.name}",
        speaker=AgentIdentity(name=agent_run.primer_speaker, constitution_version="0.2"),
        addressed_to="caucus",
        speech_act=agent_run.primer_act,
        content=UtteranceContent(body=agent_run.primer_body),
    )

    start = time.monotonic()
    try:
        await bus.publish(primer)
        try:
            response = await asyncio.wait_for(anext(observer), timeout=timeout)
            while response.speaker.name != agent_run.name:
                response = await asyncio.wait_for(anext(observer), timeout=timeout)
            elapsed = time.monotonic() - start
            return RunResult(
                name=agent_run.name, response=response, elapsed=elapsed, usage=usage_log
            )
        except TimeoutError:
            return RunResult(
                name=agent_run.name,
                response=None,
                elapsed=time.monotonic() - start,
                usage=usage_log,
                timed_out=True,
            )
    finally:
        await agent.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await memory.close()


# --------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------- #


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def double_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_response(agent_run: AgentRun, result: RunResult) -> None:
    double_section(f"{agent_run.name}")
    print(f"Trigger: {agent_run.trigger_summary}")
    if result.timed_out:
        print(f"\n  TIMEOUT after {result.elapsed:.2f}s — no response from {agent_run.name}")
        return
    assert result.response is not None
    u = result.response
    print(
        f"\n  decision: {u.speech_act.value}    elapsed: {result.elapsed:.2f}s    "
        f"input: {sum(uu.input_tokens for uu in result.usage)}  "
        f"output: {sum(uu.output_tokens for uu in result.usage)}"
    )
    body = u.content.body.strip()
    if body:
        section("Body")
        for line in body.splitlines():
            print(f"  {line}")
    if u.content.artifacts:
        section(f"Artifacts ({len(u.content.artifacts)})")
        for artifact in u.content.artifacts:
            kind = artifact.kind
            payload = artifact.payload
            title = payload.get("title", payload.get("decision_required", "?"))
            severity = payload.get("severity", payload.get("verdict", ""))
            extra = f"  [{severity}]" if severity else ""
            print(f"  - {kind}: {title}{extra}")
            path_str = payload.get("path")
            if path_str:
                path = Path(path_str)
                if path.is_file():
                    print(f"    --- {path.parent.name}/{path.name} ---")
                    for line in path.read_text(encoding="utf-8").splitlines():
                        print(f"    {line}")


def print_summary(results: list[tuple[AgentRun, RunResult]]) -> None:
    double_section("Sweep summary")
    print(f"\n  {'agent':<18s}  {'decision':<16s}  {'elapsed':>9s}  {'in':>7s}  {'out':>7s}")
    print(f"  {'-' * 18}  {'-' * 16}  {'-' * 9}  {'-' * 7}  {'-' * 7}")
    for agent_run, result in results:
        if result.timed_out:
            decision = "TIMEOUT"
        elif result.response is None:
            decision = "(no response)"
        else:
            decision = result.response.speech_act.value
        in_tokens = sum(u.input_tokens for u in result.usage)
        out_tokens = sum(u.output_tokens for u in result.usage)
        print(
            f"  {agent_run.name:<18s}  {decision:<16s}  "
            f"{result.elapsed:>7.2f}s  {in_tokens:>7d}  {out_tokens:>7d}"
        )


# --------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------- #


async def run_sweep(project_root: Path, *, timeout: float) -> int:
    print("=" * 72)
    print("Wonderland — Voices Sweep (six P5 agents, in isolation)")
    print("=" * 72)
    print(f"Project root: {project_root}")
    section("Root scenario (every per-agent trigger derives from this)")
    print(ROOT_DIRECTIVE)

    results: list[tuple[AgentRun, RunResult]] = []
    for agent_run in SWEEP:
        result = await run_one_agent(agent_run, project_root, timeout=timeout)
        print_response(agent_run, result)
        sys.stdout.flush()
        results.append((agent_run, result))

    print_summary(results)

    timeouts = [name for name, r in [(ar.name, r) for ar, r in results] if r.timed_out]
    return 1 if timeouts else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all six P5 agents in isolation.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Where to write .wonderland/ artifacts. Default: a fresh tempdir.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Per-agent timeout in seconds (default 120).",
    )
    args = parser.parse_args()

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-voices-sweep-") as tmp:
            return asyncio.run(run_sweep(Path(tmp), timeout=args.timeout))
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(run_sweep(args.project_root, timeout=args.timeout))


if __name__ == "__main__":
    sys.exit(main())
