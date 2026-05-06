"""T38 Session 1: build translation-chat features ON TOP of a working
fullstack-fastapi-react skeleton.

Differs from the T36 enchilada in two ways:

1. Pre-seeds project_root from src/wonderland/templates/fullstack-
   fastapi-react/ — a working hello-world FastAPI + SQLite + React +
   Vite app — and commits the seed as the initial git state. The team
   reads the existing code via read_file and extends it via
   write_file; Caterpillar reviews diffs against the seed baseline.

2. project_root is intended to PERSIST across sessions. Session 2 and
   Session 3 (separate scripts) reuse the same .wonderland/ directory
   (memory + registries persist) and the same source tree. Default
   path is /tmp/t38-multi-session/ so re-running Session 1 with the
   same arg overwrites cleanly.

Sequence (5 meetings, re-split post analysis-023):
1. Scoping (Alice + Cat + Queen + Dodo)            — stories + ADR + GDPR rulings
2. Decomposition (Rabbit + Cat + Dodo)             — tickets
3. Contract negotiation (Tweedles + Dodo)          — contract notes (no tools used)
4. Implementation (Tweedles + Dodo, tools-on)      — code (DIFF against seed)
5. Review (Caterpillar + Tweedles + Dodo)          — findings against git_diff

History: this used to be 5 meetings, then merged into 4 post-021
because the wall-clock quiescence model kept killing M3 mid-tool-loop.
Analysis 023 re-split them after turn-based quiescence (commit
305d3b2) made the merger unnecessary AND counterproductive — the
merged meeting closed after the design phase only, with Tweedles never
progressing to actual implementation. The split-with-turn-based-
quiescence shape: M3 holds open until contracts reach state=agreed,
M4 holds open until code ships, neither can close prematurely.

Each meeting passes its own convenor_directive (T36 v14+ pattern —
necessary post-`is_seed` so downstream meetings have a fresh-engagement
signal).
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
    "Build the translation-chat MVP features ON TOP of the existing "
    "skeleton. The codebase already exists in the working tree — "
    "FastAPI backend (src/backend/), SQLAlchemy models, React+Vite "
    "frontend (frontend/src/), pytest baseline. Health endpoint and "
    "an echo /api/messages flow are wired end-to-end already. Read "
    "what's there before designing the additions.\n\n"
    "Feature scope: two users in different language groups exchanging "
    "short text messages with near-real-time translation. EU consumer "
    "scope (GDPR applies). Two language pairs at launch (English ↔ "
    "German, English ↔ Japanese). No message edit, no delete, basic "
    "auth. Replace the placeholder HelloMessage model + /api/messages "
    "echo endpoint with the real translation-chat surface; extend the "
    "frontend App.tsx with the real UI. The team should read "
    "src/backend/models.py, src/backend/api/messages.py, and "
    "frontend/src/App.tsx first."
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


def _commit_session_baseline(project_root: Path, message: str) -> None:
    """Stage everything and commit, so the next session starts from a
    clean working tree. No-op when there are no changes (treats
    'nothing to commit' as success rather than an error).
    """
    if not (project_root / ".git").exists():
        return
    subprocess.run(
        ["git", "add", "-A"], cwd=project_root,
        capture_output=True, check=False, timeout=10,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=project_root,
        capture_output=True, text=True, check=False, timeout=10,
    )
    if not status.stdout.strip():
        print(f"Inter-session commit: nothing to commit in {project_root}")
        return
    result = subprocess.run(
        ["git", "commit", "-m", message], cwd=project_root,
        capture_output=True, text=True, check=False, timeout=10,
    )
    if result.returncode == 0:
        print(f"Inter-session commit: '{message}' in {project_root}")
    else:
        print(
            f"Inter-session commit: skipped ({result.stderr.strip() or 'no changes'})"
        )


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
        # quiescence_seconds is now the WALL-CLOCK FALLBACK for hung
        # LLM calls — turn-based quiescence (analysis 022 follow-up)
        # fires the moment all members go IDLE. 300s is the new default
        # and gives turn-based plenty of headroom to fire first; only
        # a genuinely hung deliberate() will hit this safety net.
        quiescence_seconds=300.0,
    )

    print("=" * 78)
    print("T38 SESSION 1 — translation chat features ON TOP of fullstack seed")
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

        # MEETING 3: CONTRACT NEGOTIATION — Tweedles + Dodo
        # Seeded with the ADR + a ticket. Tweedles negotiate Contract Notes.
        # Tools available but the directive forbids their use — this is a
        # design phase. Closure: contracts reach state=agreed.
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
                "Tweedledee, Tweedledum: this is the pair's design work. "
                "**Do NOT call write_file in this thread.** The codebase "
                "is not yet in scope — you are designing the seam, not "
                "shipping. Implementation happens in the next thread.\n\n"
                "Draft the contract notes that nail down the seam between "
                "frontend and backend for the seeded ticket. Half-formed "
                "is fine (state=proposed); your sibling fills in their "
                "side. Reach `state=agreed` on the load-bearing contracts "
                "before this meeting closes."
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
        # Closure: code shipped.
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
                "context are locked. Your move is `implementation`. "
                "**Call `write_file` to actually ship code** — the "
                "working tree is the artifact, the bus utterance is "
                "the team's record of what happened.\n\n"
                "**The codebase ALREADY EXISTS in the working tree** — "
                "fullstack-fastapi-react skeleton with a working "
                "/health endpoint, /api/messages echo, and a one-message "
                "frontend UI. Call `list_files` to see the layout, "
                "`read_file` to read what's there, `write_file` to "
                "extend. Key files to read first:\n"
                "  src/backend/models.py  (Base + HelloMessage placeholder)\n"
                "  src/backend/api/messages.py  (echo endpoint to replace)\n"
                "  src/backend/db.py  (SQLAlchemy session factory)\n"
                "  frontend/src/App.tsx  (placeholder UI)\n"
                "  frontend/src/api.ts  (fetch wrapper)\n"
                "  tests/conftest.py  (DB fixture pattern)\n\n"
                "DELETE the placeholder HelloMessage and /api/messages "
                "echo when shipping the real translation-chat models — "
                "they're in the way. EXTEND tests/test_messages.py "
                "with real coverage. Tweedledee owns frontend; "
                "Tweedledum owns backend."
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

        # Commit Session 1's work as a separate commit on top of the seed.
        # This makes Session 2's `git_diff HEAD` show ONLY Session 2's
        # additions, which is what Caterpillar will read in the review
        # meeting. Idempotent: if nothing was shipped (e.g. early-budget
        # exit), `git commit` returns non-zero and we move on.
        _commit_session_baseline(project_root, "session 1: translation chat")

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
    # Default to a persistent path so Session 2/3 can pick up the same
    # project_root + .wonderland/ accumulated memory.
    default_root = Path("/tmp/t38-multi-session")
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else default_root
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
