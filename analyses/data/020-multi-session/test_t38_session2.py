"""T38 Session 2: add user-blocking ON TOP of Session 1's translation chat.

REUSES the project_root from Session 1 (default /tmp/t38-multi-session/).
The .wonderland/ directory persists across sessions — every agent's
episodic memory + every registry (stories, ADRs, contract notes,
implementations, reviews) is the same on-disk state Session 1 left
behind. The source tree carries forward the translation-chat backend
the Tweedles built in Session 1.

The directive: add user blocking — a user can block another user;
blocked users can't send messages to the blocker; conversation
lookups don't return blocked-pair messages.

The load-bearing test for T38 is whether the team REACHES FOR prior-
session artifacts by name:
  - Cat should reference ADR-001 (asymmetric translation state
    machine) and ADR-002 (dual-language display) when reasoning
    about whether blocking interacts with translation status
  - Tweedles should read existing src/backend/api/messages.py and
    src/backend/models.py before designing the block surface
  - Tweedle implementations should EXTEND existing files, not
    rewrite them
  - Caterpillar should reference review-001/002/003 if relevant
    findings recur
  - The diff against HEAD should be small + focused (the new
    feature, not a re-architecture)

If we see those behaviors, memory compounds. If we see the team
re-derive the message envelope from scratch and ignore the existing
ADRs, memory doesn't.

Sequence (same 5-meeting shape as Session 1; sequence is the same
because the team's discipline is the same — only the directive +
the available context changes):
1. Scoping  (Alice + Cat + Queen + Dodo)
2. Decomposition (Rabbit + Cat + Dodo)
3. Contract negotiation (Tweedles + Dodo)
4. Implementation (Tweedles + Dodo, tools-on)
5. Review (Caterpillar + Tweedles + Dodo)
"""

import asyncio
import contextlib
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from wonderland.runner import Runner
from wonderland.utterance import SpeechAct, Utterance

DIRECTIVE = (
    "Add user-blocking to the existing translation chat. THIS IS A "
    "CONTINUATION SESSION — the translation-chat backend was built "
    "in a prior session and lives in the working tree. The team's "
    "memory carries over: every story, ADR, contract note, "
    "implementation, and review from the prior session is in your "
    "registries. Reach for them by name (ADR-001, ADR-002, "
    "contract-note-001 through 008, review-001 through 003) when "
    "they're load-bearing for the new work.\n\n"
    "Feature scope: a user can block another user. Blocked users "
    "cannot send messages to the blocker. Conversation lookups for "
    "either side of a blocked pair do not return the blocked pair's "
    "messages (the block is bidirectional in visibility, not "
    "symmetric in initiation — only the blocker can unblock). EU "
    "consumer scope; GDPR retention rules from the prior session "
    "apply. Out of scope: blocking notifications, block reasons, "
    "appeal flow.\n\n"
    "Read the existing surface first: src/backend/models.py "
    "(translation models from session 1), "
    "src/backend/api/messages.py (real translation handler that "
    "replaced the placeholder echo), src/backend/api/users.py (the "
    "user surface from session 1). Extend, don't rewrite. The diff "
    "against HEAD should be small and focused — a block surface, "
    "the model+migration for it, the message-flow integration, and "
    "the tests."
)


def _locate_template_dir() -> Path:
    """Find src/wonderland/templates/fullstack-fastapi-react/ via
    the wonderland package's location."""
    import wonderland

    pkg_path = Path(wonderland.__file__).resolve()
    template = pkg_path.parent / "templates" / "fullstack-fastapi-react"
    if not template.is_dir():
        raise SystemExit(f"could not locate template at {template}")
    return template


def _seed_template_into(project_root: Path) -> None:
    """Copy the fullstack template into project_root and commit as
    the initial git state. Mirrors the T37 pattern.

    If project_root already has .git, treat it as a continuation run
    (Session 2 / Session 3) and skip — the seed is already there from
    Session 1."""
    if (project_root / ".git").exists():
        print(f"Pre-seed:      {project_root} already has .git — skipping seed copy")
        return
    template = _locate_template_dir()
    print(f"Pre-seed:      {template} → {project_root}")
    shutil.copytree(template, project_root, dirs_exist_ok=True)
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=project_root,
                   capture_output=True, check=True, timeout=10)
    subprocess.run(["git", "config", "user.email", "wonderland@local"],
                   cwd=project_root, capture_output=True, check=True, timeout=10)
    subprocess.run(["git", "config", "user.name", "Wonderland Runner"],
                   cwd=project_root, capture_output=True, check=True, timeout=10)
    subprocess.run(["git", "add", "."], cwd=project_root,
                   capture_output=True, check=True, timeout=10)
    subprocess.run(
        ["git", "commit", "-m",
         "seed: fullstack-fastapi-react baseline (T38 Session 1)"],
        cwd=project_root, capture_output=True, check=True, timeout=10,
    )


class Capture:
    """Accumulates substantive utterances across meetings so prior-meeting
    artifacts can seed follow-up meetings."""

    def __init__(self) -> None:
        self.utterances: list[Utterance] = []

    def observe(self, u: Utterance) -> None:
        # Only keep utterances that carried artifacts (the substantive ones).
        # The seed needs to carry the artifact; we don't need every concern.
        if u.content.artifacts:
            self.utterances.append(u)

    def by_kind(self, *kinds: str) -> list[Utterance]:
        return [
            u for u in self.utterances if any(a.kind in kinds for a in u.content.artifacts)
        ]


def render_event(event, label: str = "") -> str | None:
    """Format an event for the live-watch output. Returns None to skip."""
    elapsed = event.elapsed
    prefix = f"  {label}" if label else ""
    if event.kind == "utterance":
        u = event.payload["utterance"]
        first_line = u.content.body.strip().split("\n", 1)[0] if u.content.body else "(no body)"
        snippet = first_line[:100] + ("…" if len(first_line) > 100 else "")
        addressed = (
            u.addressed_to
            if isinstance(u.addressed_to, str)
            else "[" + ",".join(a.name for a in u.addressed_to) + "]"
        )
        line = f"{prefix}[t={elapsed:6.2f}s] {u.speaker.name:18s} {u.speech_act.value:14s} →{addressed} {snippet}"
        if u.content.artifacts:
            for art in u.content.artifacts:
                title = art.payload.get("title", "?")
                meta_bits = []
                for key in ("operation", "state", "side", "severity"):
                    val = art.payload.get(key)
                    if val:
                        meta_bits.append(f"{key}={val}")
                meta = f" [{', '.join(meta_bits)}]" if meta_bits else ""
                line += f"\n{prefix}{'':<29s}↳ {art.kind}: {title}{meta}"
        return line
    if event.kind == "state":
        change = event.payload["change"]
        return f"{prefix}[t={elapsed:6.2f}s] <thread_monitor> {change.from_state.value} → {change.to_state.value}"
    if event.kind == "complete":
        return f"{prefix}[t={elapsed:6.2f}s] <complete>"
    if event.kind == "timeout":
        return f"{prefix}[t={elapsed:6.2f}s] <timeout>"
    if event.kind == "aborted":
        return f"{prefix}[t={elapsed:6.2f}s] <aborted>"
    if event.kind == "budget_exceeded":
        cost = event.payload["cost"]
        return f"{prefix}[t={elapsed:6.2f}s] <budget> EXCEEDED ${cost:.2f}"
    if event.kind == "budget_warning":
        cost = event.payload["cost"]
        budget = event.payload["budget"]
        return f"{prefix}[t={elapsed:6.2f}s] <budget> WARNING ${cost:.2f} / ${budget:.2f}"
    return None


async def run_meeting(
    runner: Runner,
    *,
    thread_id: str,
    goal: str,
    roster: list[str],
    seeds: list[Utterance],
    convenor_directive: str | None = None,
    capture: Capture,
    label: str,
    meeting_budget: float | None = None,
) -> None:
    """Convene a meeting + drain events until it terminates.

    ``meeting_budget`` is a per-meeting cap on additional spend. When
    the meeting's spend exceeds the cap, we end the meeting early so
    one chatty meeting can't starve the rest. Independent of (and
    tighter than) the Runner's global budget cap.
    """
    # Reset the Runner's per-thread completion tracking so it can fire
    # complete again for this new thread.
    runner._completed = False

    cost_before = runner.total_cost
    calls_before = runner.telemetry.call_count
    artifact_count_before = sum(
        1 for u in capture.utterances if u.content.artifacts
    )
    meeting_start = time.monotonic()

    print()
    print("─" * 78)
    print(f"MEETING {label}: {goal}")
    print(f"  thread_id: {thread_id}")
    print(f"  roster:    {sorted(set(roster) | {'dodo'})}")
    print(f"  seeds:     {len(seeds)} utterance(s)")
    print(f"  cost so far before this meeting: ${cost_before:.4f}")
    print("─" * 78)

    await runner.convene(
        thread_id=thread_id,
        goal=goal,
        roster=roster,
        seed_utterances=seeds,
        convenor_directive=convenor_directive,
    )

    async for event in runner.events():
        if event.kind == "utterance":
            capture.observe(event.payload["utterance"])
        line = render_event(event, label=label)
        if line:
            print(line)
            sys.stdout.flush()
        if event.kind == "budget_exceeded":
            _print_meeting_summary(
                runner, capture, label, meeting_start,
                cost_before, calls_before, artifact_count_before, "GLOBAL_BUDGET",
            )
            return
        # Per-meeting budget cap — soft, but enforced by ending early.
        # The Runner's global hard cap still applies on top.
        if meeting_budget is not None:
            spent = runner.total_cost - cost_before
            if spent >= meeting_budget:
                print(
                    f"  {label}[per-meeting cap] ${spent:.4f} >= ${meeting_budget:.2f}; "
                    f"ending meeting to preserve budget for downstream meetings"
                )
                _print_meeting_summary(
                    runner, capture, label, meeting_start,
                    cost_before, calls_before, artifact_count_before, "MEETING_BUDGET",
                )
                return
        if event.kind in ("complete", "timeout", "aborted"):
            outcome = event.kind.upper()
            _print_meeting_summary(
                runner, capture, label, meeting_start,
                cost_before, calls_before, artifact_count_before, outcome,
            )
            return


def _print_meeting_summary(
    runner: Runner,
    capture: Capture,
    label: str,
    meeting_start: float,
    cost_before: float,
    calls_before: int,
    artifact_count_before: int,
    outcome: str,
) -> None:
    elapsed = time.monotonic() - meeting_start
    cost_delta = runner.total_cost - cost_before
    calls_delta = runner.telemetry.call_count - calls_before
    artifacts_after = sum(1 for u in capture.utterances if u.content.artifacts)
    new_artifacts = artifacts_after - artifact_count_before
    # Tally artifact kinds produced during this meeting.
    new_capture = capture.utterances[artifact_count_before:]  # rough; safe-enough
    kinds_count: dict[str, int] = {}
    for u in new_capture:
        for a in u.content.artifacts:
            kinds_count[a.kind] = kinds_count.get(a.kind, 0) + 1
    print()
    print(f"  ── {label} END ── outcome={outcome}")
    print(f"     elapsed:        {elapsed:.1f}s")
    print(f"     this meeting:   {calls_delta} calls, ${cost_delta:.4f}")
    print(
        f"     running totals: {runner.telemetry.call_count} calls, ${runner.total_cost:.4f} / "
        f"${runner.budget_dollars:.2f} cap"
    )
    if kinds_count:
        kinds_str = ", ".join(f"{k}×{v}" for k, v in sorted(kinds_count.items(), key=lambda kv: -kv[1]))
        print(f"     artifacts:      {new_artifacts} ({kinds_str})")
    else:
        print(f"     artifacts:      0")


async def main(project_root: Path) -> int:
    # Seed the fullstack template + commit BEFORE Runner.make_full_cast.
    # The Runner's _ensure_git_repo is idempotent on .git existing, so
    # it won't clobber. Skipped on continuation runs (Session 2/3 same
    # project_root → .git already exists).
    _seed_template_into(project_root)

    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=3.00,
        timeout_seconds=900.0,
        # Bumped from 30s to 60s to give Tweedles' tool-use loops time
        # to complete before a meeting quiesces. v17 diagnostic showed
        # M3 closing at exactly 30s with Tweedle responses landing
        # ~0.3s late — their contract_notes got published to the
        # already-closed thread, lost from the script's capture.
        # Workaround pending the Dodo meeting-orchestration redesign
        # (roadmap item — Dodo tracks per-agent deliberation pending,
        # holds the meeting open while expected responses are in
        # flight).
        quiescence_seconds=60.0,
    )

    print("=" * 78)
    print("T38 SESSION 2 — user-blocking ON TOP of Session 1's translation chat")
    print("=" * 78)
    print(f"Project root:  {project_root}")
    print(f"Budget cap:    $3.00 hard")
    print(f"Total timeout: 900s")
    print(f"Directive:     {DIRECTIVE[:100]}...")

    capture = Capture()
    start = time.monotonic()

    try:
        await runner.setup()

        # MEETING 1: SCOPING — Alice + Cat + Queen + Dodo
        # Vague directive in; expect stories from Alice + ADR(s) from Cat
        # + GDPR/security rulings from Queen.
        await run_meeting(
            runner,
            thread_id="scoping",
            goal="produce user stories + an architectural ADR + GDPR rulings",
            roster=["alice", "cheshire_cat", "queen_of_hearts"],
            seeds=[],
            convenor_directive=DIRECTIVE,
            capture=capture,
            label="M1",
            meeting_budget=0.40,
        )
        if runner.total_cost >= runner.budget_dollars * 0.95:
            print(f"\n  budget consumed by meeting 1; stopping at ${runner.total_cost:.2f}")
            return 0

        # MEETING 2: DECOMPOSITION — Rabbit + Cat + Dodo
        # Seeded with ADR(s) and stories from M1; Rabbit decomposes into tickets.
        m2_seeds = capture.by_kind("adr") + capture.by_kind("story")
        await run_meeting(
            runner,
            thread_id="decomposition",
            goal="decompose the ADR + stories into v1 tickets",
            roster=["white_rabbit", "cheshire_cat"],
            seeds=m2_seeds,
            convenor_directive=(
                "Decomposition thread. CONTINUATION SESSION — your "
                "registries already hold session-1 ADRs (ADR-001: "
                "asymmetric translation; ADR-002: dual-language "
                "display + polling sync), tickets, and contract "
                "notes. The new stories about user-blocking just "
                "landed. Rabbit: decompose the BLOCKING work, "
                "referencing existing tickets where it composes. "
                "Cat: weigh in only if blocking implies a fresh "
                "architectural decision ADR-001/002 don't already "
                "cover. If extending an existing ADR is enough, "
                "say so explicitly — don't ship a redundant ADR."
            ),
            capture=capture,
            label="M2",
            meeting_budget=0.30,
        )
        if runner.total_cost >= runner.budget_dollars * 0.95:
            print(f"\n  budget consumed by meeting 2; stopping at ${runner.total_cost:.2f}")
            return 0

        # MEETING 3: CONTRACT NEGOTIATION — Tweedles + Cat + Dodo
        # Seeded with the ADR + a ticket. Tweedles negotiate Contract Notes.
        # Pick the FIRST ticket (decomposition usually produces several;
        # one is enough to get the contract negotiation started).
        adr_seeds = capture.by_kind("adr")
        ticket_seeds = capture.by_kind("ticket")[:1]  # first ticket only
        await run_meeting(
            runner,
            thread_id="contract-negotiation",
            goal="negotiate contracts the Tweedles will implement against",
            roster=["tweedledee", "tweedledum"],
            seeds=adr_seeds + ticket_seeds,
            convenor_directive=(
                "Contract negotiation thread. CONTINUATION SESSION — "
                "your registries hold session-1 contract notes "
                "(contract-note-001 through 008: message envelope, "
                "polling, language display, translation failure, "
                "etc.). The blocking surface adds a new seam: where "
                "does the block check fire (endpoint? service "
                "layer? query filter?) and what's the contract "
                "between the block-state read and the message-flow "
                "write?\n\n"
                "Reference existing contract notes by number when "
                "composing — if your new contract extends "
                "contract-note-001's envelope, say so. Half-formed "
                "is fine; reach `state=agreed` on the load-bearing "
                "block contract before this meeting closes."
            ),
            capture=capture,
            label="M3",
            meeting_budget=0.80,
        )
        if runner.total_cost >= runner.budget_dollars * 0.95:
            print(f"\n  budget consumed by meeting 3; stopping at ${runner.total_cost:.2f}")
            return 0

        # MEETING 4: IMPLEMENTATION — Tweedles + Dodo
        # Seeded with the ADR + agreed contract notes. Tools on (write_file).
        contract_seeds = capture.by_kind("contract_note")
        # Filter to agreed contracts only — those are the locked ones to
        # implement against.
        agreed_contracts = [
            u
            for u in contract_seeds
            if any(
                a.kind == "contract_note" and a.payload.get("state") == "agreed"
                for a in u.content.artifacts
            )
        ]
        await run_meeting(
            runner,
            thread_id="implementation",
            goal="ship code honoring the agreed contracts",
            roster=["tweedledee", "tweedledum"],
            seeds=adr_seeds + (agreed_contracts or contract_seeds),
            convenor_directive=(
                "Implementation thread. The contract notes in your "
                "context are locked. Your move is `implementation`.\n\n"
                "**THE CODEBASE IS NOT EMPTY** — Session 1 shipped the "
                "translation-chat backend (real models in "
                "src/backend/models.py, real handler in "
                "src/backend/api/messages.py, user surface in "
                "src/backend/api/users.py, schemas in "
                "src/backend/api/schemas.py, tests in "
                "tests/test_messages.py). Call `list_files` to see "
                "the layout; `read_file` the existing models, "
                "endpoints, and schemas before designing the block "
                "surface; `git_status` to see what's modified vs "
                "what's untouched.\n\n"
                "EXTEND don't rewrite. The block feature lives "
                "alongside the existing message flow, not as a "
                "replacement. Add a Block model to models.py "
                "(reusing the Base from session 1), wire the block "
                "check into messages.py's send + list endpoints, "
                "extend tests/test_messages.py with block-pair "
                "coverage. Tweedledee owns frontend; Tweedledum owns "
                "backend. The diff against HEAD should be small and "
                "focused — if you're rewriting more than ~100 lines "
                "of session-1 code, you're probably re-architecting "
                "instead of extending."
            ),
            capture=capture,
            label="M4",
            meeting_budget=1.00,
        )
        if runner.total_cost >= runner.budget_dollars * 0.95:
            print(f"\n  budget consumed by meeting 4; stopping at ${runner.total_cost:.2f}")
            return 0

        # MEETING 5: REVIEW — Caterpillar + Tweedles + Dodo
        # Caterpillar reads the shipped code via tools, surfaces findings.
        impl_seeds = capture.by_kind("implementation")
        await run_meeting(
            runner,
            thread_id="review",
            goal="Caterpillar reviews the shipped code; surface findings",
            roster=["caterpillar", "tweedledee", "tweedledum"],
            seeds=impl_seeds,
            convenor_directive=(
                "Review thread. CONTINUATION SESSION — Caterpillar's "
                "registry already holds review-001/002/003 from "
                "session 1. The working tree carries forward "
                "session 1's work AND the new blocking feature. "
                "Call `git_status` to see what's modified since "
                "HEAD; `git_diff` to read the new changes "
                "specifically.\n\n"
                "Caterpillar: review the BLOCKING diff on its own "
                "merits — but if a finding mirrors one you raised "
                "in session 1's reviews (e.g., the same anti-"
                "pattern recurred in the block-check code), say so "
                "and reference the prior review by number. Tweedles: "
                "respond to findings; if a finding implies a code "
                "change you agree with, ship the fix via "
                "`write_file` and re-emit an `implementation` "
                "utterance. Don't re-litigate locked contracts."
            ),
            capture=capture,
            label="M5",
            meeting_budget=0.50,
        )

    finally:
        elapsed_total = time.monotonic() - start
        await runner.teardown()

        # Summary
        print()
        print("=" * 78)
        print("T38 SESSION 2 SUMMARY")
        print("=" * 78)
        print(f"Total elapsed:  {elapsed_total:.1f}s")
        print(f"Total cost:     ${runner.total_cost:.4f}  (cap ${runner.budget_dollars:.2f})")
        print(f"Total LLM calls: {runner.telemetry.call_count}")
        print()
        print("Per-agent token usage:")
        for agent, row in sorted(
            runner.telemetry.per_agent_summary().items(),
            key=lambda kv: -float(kv[1]["cost"]),
        ):
            print(
                f"  {agent:18s} calls={int(row['calls']):3d} "
                f"cost=${float(row['cost']):.4f}"
            )
        print()
        print("Artifacts on disk:")
        for subdir in (
            "stories",
            "architecture",
            "tickets",
            "test-scenarios",
            "rulings",
            "observations",
            "implementations",
            "contract-notes",
            "reviews",
            "escalations",
        ):
            path = project_root / ".wonderland" / subdir
            if path.is_dir():
                files = sorted(path.glob("*.md"))
                if files:
                    print(f"  {subdir}/ ({len(files)} files)")
                    for f in files:
                        print(f"    {f.name}")
        print()
        print("Code shipped (project_root excluding .wonderland):")
        for f in sorted(project_root.rglob("*")):
            if f.is_file() and ".wonderland" not in f.parts:
                rel = f.relative_to(project_root)
                print(f"  {rel} ({f.stat().st_size} bytes)")

        print()
        print("Final rosters:")
        for thread in runner.roster.threads():
            members = sorted(runner.roster.members(thread))
            goal = runner.roster.goal(thread)
            print(f"  {thread}: {members} — {goal[:60]}")

    return 0


if __name__ == "__main__":
    # Default to a persistent path so Session 2/3 can pick up the same
    # project_root + .wonderland/ accumulated memory.
    default_root = Path("/tmp/t38-multi-session")
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else default_root
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
