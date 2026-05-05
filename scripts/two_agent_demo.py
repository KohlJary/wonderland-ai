"""Run the Cat + Rabbit dance once with real LLMs and print everything.

Usage:
    uv run python scripts/two_agent_demo.py
    uv run python scripts/two_agent_demo.py --directive "Build a thing..."
    uv run python scripts/two_agent_demo.py --project-root ./demo-output --compact

When ``--compact`` is set, after the dance settles each agent runs
``compact(thread_id)`` against the same LLM and the resulting semantic
+ relational updates are printed.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
import tempfile
import time
from pathlib import Path

from wonderland import (
    ADRRegistry,
    AgentIdentity,
    AgentMemory,
    CheshireCat,
    CompactionResult,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    TicketRegistry,
    TokenUsage,
    Utterance,
    UtteranceContent,
    WhiteRabbit,
)

DEFAULT_DIRECTIVE = (
    "Build a translation-integrated chat application. Initial scope: "
    "two users in different language groups exchanging short messages "
    "with near-real-time translation."
)
DEFAULT_TIMEOUT_S = 60.0


def section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_utterance(u: Utterance, *, elapsed: float | None = None) -> None:
    suffix = f", {elapsed:.2f}s" if elapsed is not None else ""
    print(f"\n[{u.speaker.name} — {u.speech_act.value}{suffix}]")
    print(u.content.body)
    if u.content.artifacts:
        print(f"\n  Artifacts ({len(u.content.artifacts)}):")
        for artifact in u.content.artifacts:
            print(f"    - {artifact.kind}: {artifact.payload.get('title', artifact.payload)}")
            if artifact.kind in {"adr", "ticket"} and "path" in artifact.payload:
                path = Path(artifact.payload["path"])
                if path.is_file():
                    print(f"      → {path.relative_to(path.parent.parent.parent.parent)}")


def print_compaction(name: str, result: CompactionResult, memory: AgentMemory) -> None:
    print(f"\n## {name} compaction")
    if result.is_empty:
        print("  (no updates — uneventful for this agent or already settled)")
        return
    if result.semantic_topics_updated:
        print("\n  semantic updates:")
        for topic in result.semantic_topics_updated:
            content = memory.semantic.read(topic)
            print(f"    ### {topic}")
            for line in content.splitlines():
                print(f"      {line}")
    if result.relational_agents_updated:
        print("\n  relational updates:")
        for agent_name in result.relational_agents_updated:
            content = memory.relational.read(agent_name)
            print(f"    ### {agent_name}")
            for line in content.splitlines():
                print(f"      {line}")


async def run_demo(
    directive: str,
    project_root: Path,
    *,
    timeout: float,
    compact: bool,
) -> int:
    print("=" * 70)
    print("Wonderland — Cat + Rabbit demo")
    print("=" * 70)
    print(f"Project root: {project_root}")

    usage_log: list[tuple[str, TokenUsage]] = []

    def on_cat_usage(u: TokenUsage) -> None:
        usage_log.append(("cat", u))

    def on_rabbit_usage(u: TokenUsage) -> None:
        usage_log.append(("rabbit", u))

    bus = InMemoryCaucus()
    cat_memory = AgentMemory.for_project(project_root, "cheshire_cat")
    rabbit_memory = AgentMemory.for_project(project_root, "white_rabbit")
    await cat_memory.open()
    await rabbit_memory.open()

    cat = CheshireCat(
        memory=cat_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=on_cat_usage),
        adr_registry=ADRRegistry(project_root),
    )
    rabbit = WhiteRabbit(
        memory=rabbit_memory,
        bus=bus,
        llm=LLMClient(on_token_usage=on_rabbit_usage),
        ticket_registry=TicketRegistry(project_root),
    )
    observer = bus.subscribe(agent_name="observer")
    cat_task = asyncio.create_task(cat.run())
    rabbit_task = asyncio.create_task(rabbit.run())

    section("Directive")
    print(directive)

    dodo = AgentIdentity(name="dodo", constitution_version="0.2")
    thread_id = "demo-thread"
    start = time.monotonic()
    await bus.publish(
        Utterance(
            thread_id=thread_id,
            speaker=dodo,
            addressed_to="caucus",
            speech_act=SpeechAct.DIRECTIVE,
            content=UtteranceContent(body=directive),
        )
    )

    section("Dance")
    exit_code = 0
    seen: dict[str, Utterance] = {}
    seen_at: dict[str, float] = {}
    try:
        deadline = start + timeout
        while {"cheshire_cat", "white_rabbit"} - set(seen.keys()):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            u = await asyncio.wait_for(anext(observer), timeout=remaining)
            if u.speaker.name in {"cheshire_cat", "white_rabbit"} and u.speaker.name not in seen:
                seen[u.speaker.name] = u
                seen_at[u.speaker.name] = time.monotonic() - start

        for name in ("cheshire_cat", "white_rabbit"):
            if name in seen:
                print_utterance(seen[name], elapsed=seen_at[name])
            else:
                print(f"\n[{name}] did not speak within {timeout:.0f}s")
                exit_code = 1

        if usage_log:
            section("Token usage (per call)")
            for who, u in usage_log:
                print(
                    f"  {who:7s}: input={u.input_tokens:5d} "
                    f"output={u.output_tokens:4d} "
                    f"cache_read={u.cache_read_input_tokens:5d}"
                )
    except TimeoutError:
        print(f"\nTIMEOUT: dance did not complete within {timeout:.0f}s", file=sys.stderr)
        exit_code = 1

    if compact and exit_code == 0:
        section("Compaction (each agent reflects)")
        # Stop the run loops so compaction has the field — agents shouldn't be
        # processing new utterances while reflecting on the just-completed thread.
        await cat.stop()
        await rabbit.stop()

        cat_compaction = await cat.compact(thread_id)
        rabbit_compaction = await rabbit.compact(thread_id)

        print_compaction("Cheshire Cat", cat_compaction, cat_memory)
        print_compaction("White Rabbit", rabbit_compaction, rabbit_memory)
    else:
        await cat.stop()
        await rabbit.stop()

    cat_task.cancel()
    rabbit_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cat_task
    with contextlib.suppress(asyncio.CancelledError):
        await rabbit_task
    await cat_memory.close()
    await rabbit_memory.close()
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Cat + Rabbit dance once.")
    parser.add_argument("--directive", default=DEFAULT_DIRECTIVE)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Where to write .wonderland/ artifacts. Default: a fresh tempdir.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_S,
        help=f"Seconds to wait for the dance (default {DEFAULT_TIMEOUT_S:.0f}).",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="After the dance, run each agent's compact() and print updates.",
    )
    args = parser.parse_args()

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-two-agent-demo-") as tmp:
            return asyncio.run(
                run_demo(args.directive, Path(tmp), timeout=args.timeout, compact=args.compact)
            )
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(
        run_demo(args.directive, args.project_root, timeout=args.timeout, compact=args.compact)
    )


if __name__ == "__main__":
    sys.exit(main())
