"""Run Alice once with a real LLM and print everything she produces.

Usage:
    uv run python scripts/alice_demo.py
    uv run python scripts/alice_demo.py --directive "Build a thing..."
    uv run python scripts/alice_demo.py --project-root ./demo-output

Mirrors scripts/cat_demo.py. Default directive is the translation-chat
one used across the other demos so the cross-character comparison
holds.
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
    AgentIdentity,
    AgentMemory,
    Alice,
    InMemoryCaucus,
    LLMClient,
    SpeechAct,
    StoryRegistry,
    TokenUsage,
    Utterance,
    UtteranceContent,
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


async def run_demo(directive: str, project_root: Path, *, timeout: float) -> int:
    print("=" * 70)
    print("Wonderland — Alice demo")
    print("=" * 70)
    print(f"Project root: {project_root}")

    usage_log: list[TokenUsage] = []

    def on_usage(u: TokenUsage) -> None:
        usage_log.append(u)

    bus = InMemoryCaucus()
    memory = AgentMemory.for_project(project_root, "alice")
    await memory.open()
    registry = StoryRegistry(project_root)
    llm = LLMClient(on_token_usage=on_usage)

    alice = Alice(memory=memory, bus=bus, llm=llm, story_registry=registry)
    observer = bus.subscribe(agent_name="observer")
    run_task = asyncio.create_task(alice.run())

    section("Directive")
    print(directive)

    dodo = AgentIdentity(name="dodo", constitution_version="0.2")
    start = time.monotonic()
    await bus.publish(
        Utterance(
            thread_id="demo-thread",
            speaker=dodo,
            addressed_to="caucus",
            speech_act=SpeechAct.DIRECTIVE,
            content=UtteranceContent(body=directive),
        )
    )

    exit_code = 0
    try:
        response = await asyncio.wait_for(anext(observer), timeout=timeout)
        while response.speaker.name != "alice":
            response = await asyncio.wait_for(anext(observer), timeout=timeout)
        elapsed = time.monotonic() - start

        section(f"Alice response  [{response.speech_act.value}, {elapsed:.2f}s]")
        print(response.content.body)

        if response.content.artifacts:
            section(f"Stories ({len(response.content.artifacts)})")
            for artifact in response.content.artifacts:
                if artifact.kind != "story":
                    continue
                path = Path(artifact.payload["path"])
                if path.is_file():
                    print()
                    print(f"--- {path.name} ---")
                    print(path.read_text(encoding="utf-8"), end="")
        else:
            section("Stories")
            print("(none — Alice chose a non-story decision)")

        if usage_log:
            u = usage_log[0]
            section("Token usage")
            print(f"  input:           {u.input_tokens}")
            print(f"  output:          {u.output_tokens}")
            print(f"  cache_creation:  {u.cache_creation_input_tokens}")
            print(f"  cache_read:      {u.cache_read_input_tokens}")

        section("Timing")
        print(f"  end-to-end: {elapsed:.2f}s")

    except TimeoutError:
        print(f"\nTIMEOUT: no Alice utterance within {timeout:.0f}s", file=sys.stderr)
        exit_code = 1
    finally:
        await alice.stop()
        run_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await run_task
        await memory.close()

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Alice once.")
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
        help=f"Seconds to wait for Alice's response (default {DEFAULT_TIMEOUT_S:.0f}).",
    )
    args = parser.parse_args()

    if args.project_root is None:
        with tempfile.TemporaryDirectory(prefix="wonderland-alice-demo-") as tmp:
            return asyncio.run(run_demo(args.directive, Path(tmp), timeout=args.timeout))
    args.project_root.mkdir(parents=True, exist_ok=True)
    return asyncio.run(run_demo(args.directive, args.project_root, timeout=args.timeout))


if __name__ == "__main__":
    sys.exit(main())
