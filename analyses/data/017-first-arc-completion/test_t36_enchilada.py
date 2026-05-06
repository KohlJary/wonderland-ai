"""T36 full enchilada: vague directive → working code via multi-meeting flow.

Sequence:
1. Scoping (Alice + Cat + Queen): produce stories + ADR
2. Decomposition (Rabbit + Cat, seeded with ADR + stories): produce tickets
3. Contract negotiation (Tweedles + Cat, seeded with ADR + a ticket): contracts
4. Implementation (Tweedles, tools-on, seeded with contracts + ADR): ship code
5. Review (Caterpillar + Tweedles, Caterpillar can read the shipped code)

Each meeting is a separate convene() call on the same Runner instance.
Prior-meeting artifacts are scooped from the captured utterance stream
and re-published as seeds for the next meeting. Hatter, Dormouse can
get buzzed in via INVITE if any agent decides they're needed.
"""

import asyncio
import contextlib
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

from wonderland.runner import Runner
from wonderland.utterance import SpeechAct, Utterance

DIRECTIVE = (
    "Build a translation-integrated chat application MVP. Two users in "
    "different language groups exchanging short messages with near-real-"
    "time translation. EU consumer scope (GDPR applies). Target: "
    "shippable v1 in three weeks. Initial scope: text-only messages, "
    "two-language pairs at launch (English ↔ German, English ↔ Japanese), "
    "no message edit, no message delete, basic auth. Looking for the team "
    "to scope, decompose, and ship the load-bearing seam."
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
    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=3.00,
        timeout_seconds=900.0,
        quiescence_seconds=30.0,
    )

    print("=" * 78)
    print("T36 FULL ENCHILADA — vague directive → working code via 5 meetings")
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
                "Decomposition thread. The stories and ADR(s) in your "
                "context are settled — they were produced in a prior "
                "scoping thread. Read them as locked context, not as "
                "fresh proposals to respond to. Rabbit, your move is "
                "`ticket`: decompose the user-story-and-architecture "
                "picture into v1-scope work units the Tweedles can pick "
                "up. Cat, weigh in only if a ticket implies a fresh "
                "architectural decision the existing ADRs don't cover."
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
                "Contract negotiation thread. The ADR(s) and ticket in "
                "your context are settled — read them as locked. "
                "Tweedledee, Tweedledum: this is the pair's work. Draft "
                "the contract notes that nail down the seam between "
                "frontend and backend for the seeded ticket. "
                "Half-formed is fine (state=proposed); your sibling "
                "fills in their side. Reach `state=agreed` on the "
                "load-bearing contracts before this meeting closes."
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
                "Implementation thread. The contract notes in your context "
                "are locked — they were negotiated and agreed in a prior "
                "thread. Do NOT propose new contract_notes or refine the "
                "existing ones; that work is done. Your move here is "
                "`implementation`: write code against the agreed contracts. "
                "Use your write_file tool. Tweedledee owns frontend; "
                "Tweedledum owns backend. Ship the load-bearing seam first."
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
                "Review thread. Code was shipped in a prior implementation "
                "thread. Caterpillar: the working tree IS the implementation "
                "artifact — call `git_status` to see what shipped, then "
                "`git_diff` to read the changes. Surface findings on the "
                "code itself, citing files and lines. Tweedles: respond "
                "to findings; if a finding implies a code change you agree "
                "with, ship the fix via `write_file` and re-emit an "
                "`implementation` utterance. Do not re-litigate the "
                "contracts; they're locked."
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
        print("T36 SUMMARY")
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
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
