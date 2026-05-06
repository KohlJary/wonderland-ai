"""T37: security recovery showcase.

A synthesized credential-stuffing incident lands as a Dormouse
observation. The full cast responds in a single bus thread:
  - Queen rules on immediate mitigation (rate-limit, lockout, etc.)
  - Cat confirms / refutes that the architectural surface is intact
  - Tweedles ship the mitigation as code in the working tree
  - Hatter writes test scenarios for the recurrence class
  - Caterpillar reviews the shipped mitigation

Per gameplan T37 acceptance:
  - Queen issues ≥1 critical-severity ruling
  - Tweedles ship ≥1 implementation responding to the ruling
  - Caterpillar reviews
  - Hatter publishes test scenarios for the recurrence class
  - Thread COMPLETE within 8 minutes
  - Per-run cost <$3

Single meeting (not 5-meeting enchilada like T36) — incidents
respond fast, no neat pre-decomposition. Tests:
  - Reactive (vs proactive) team behavior
  - Queen + Dormouse alliance
  - Mad Hatter (untested in T36)
  - Conflict ladder if Tweedle implementation conflicts with
    Queen ruling
"""

import asyncio
import contextlib
import os
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path


def _locate_seed_dir() -> Path:
    """Find the pre-seed dir. T37 v1 ran without a seed and overran
    cost by ~$0.01 because the team had to imagine the auth surface
    AND respond to the incident in the same thread. The seed gives
    them concrete code to read_file against and write_file diffs
    onto. README at analyses/data/019-security-recovery-seed/.

    Resolution order:
      1. T37_SEED_DIR environment variable (override).
      2. The wonderland package's location → repo root → analyses/data/...
    """
    override = os.environ.get("T37_SEED_DIR")
    if override:
        path = Path(override).resolve()
        if not path.is_dir():
            raise SystemExit(f"T37_SEED_DIR={override} is not a directory")
        return path
    import wonderland

    pkg_path = Path(wonderland.__file__).resolve()
    # wonderland/__init__.py → wonderland/ → src/wonderland/ → src/ → repo root
    repo_root = pkg_path.parent.parent.parent
    seed = repo_root / "analyses/data/019-security-recovery-seed"
    if not seed.is_dir():
        raise SystemExit(f"could not locate seed dir at {seed}")
    return seed


def _commit_seed_baseline(project_root: Path) -> None:
    """Initialize git in project_root and commit the seed as the
    initial state. The team's write_file calls will appear as a clean
    diff against this baseline; the seed README and source are part of
    the initial commit, not part of the team's work.

    Mirrors Runner._ensure_git_repo's setup but runs first so the seed
    files land in the initial commit. Writes .gitignore excluding
    .wonderland/ before committing so framework state stays out of
    git_diff. Skips silently if git is unavailable."""
    import subprocess

    if (project_root / ".git").exists():
        return
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# Wonderland framework state — registries, episodic memory,\n"
            "# telemetry. Not part of the code under review.\n"
            ".wonderland/\n"
        )
    try:
        subprocess.run(
            ["git", "init", "--initial-branch=main"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "config", "user.email", "wonderland@local"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "config", "user.name", "Wonderland Runner"],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "seed: baseline auth service (T37 security-recovery showcase)",
            ],
            cwd=project_root,
            capture_output=True,
            check=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(f"warning: seed-baseline commit failed: {exc} — git_diff may show extra files")

from wonderland.identity import AgentIdentity
from wonderland.observation import ObservationPayload, ObservationSeverity, ObservationType
from wonderland.runner import Runner
from wonderland.utterance import Artifact, SpeechAct, Utterance, UtteranceContent

INCIDENT_OBSERVATION_PAYLOAD = ObservationPayload(
    title=(
        "Anomalous auth-failure spike from single IP — possible "
        "credential stuffing in progress"
    ),
    type=ObservationType.INCIDENT,
    severity=ObservationSeverity.SEV1,
    time_window_start="2026-05-06T17:30:00Z",
    time_window_end="",
    symptom=(
        "auth_failures{endpoint='/login', source_ip='203.0.113.42'} = "
        "4127 in the last 8 minutes (baseline: 12 ± 4 per 8min). "
        "Username distribution = 2803 distinct accounts attempted. "
        "Success rate dropped from baseline 94% to 0.2% during this "
        "window. 47 user accounts have crossed the lockout threshold "
        "of 5 failed attempts."
    ),
    affected_scope=(
        "/login endpoint; estimated 47 user accounts now in "
        "auto-lockout state from the failed attempts; production EU "
        "region only (US region baseline)."
    ),
    evidence=[
        "grafana://prod/auth-failures?ip=203.0.113.42&window=8m  (linked to incident dashboard)",
        "loki://prod/loki?query={app=\"auth\"} |= \"203.0.113.42\" |= \"INVALID_PASSWORD\" — 4127 hits",
        "audit_log entries 2026-05-06T17:30:00Z to ongoing — 47 accounts with ≥5 failures",
        "WAF logs show requests originating from a single IP with rotating User-Agent strings — automation signature",
    ],
    probable_domain="security",
    routed_to="queen_of_hearts",
)

INCIDENT_BODY = (
    "INCIDENT — credential-stuffing pattern in progress. Production "
    "telemetry shows an anomalous auth-failure spike from "
    "source_ip=203.0.113.42 in the last 8 minutes: 4,127 failed login "
    "attempts across 2,803 distinct usernames, vs baseline 12 ± 4. "
    "Success rate dropped from 94% to 0.2% during this window. 47 "
    "user accounts have already crossed the lockout threshold (5 "
    "failed attempts). The pattern (high-volume, distinct-username, "
    "single-source IP, rotating User-Agent strings) is consistent "
    "with an automated credential-stuffing attack iterating through "
    "a leaked-credentials list against our /login endpoint. "
    "Routing to the Queen for ruling on immediate mitigation. "
    "Evidence cited in the observation payload."
)

CONVENOR_DIRECTIVE = (
    "Security incident response thread. The Dormouse just published an "
    "observation indicating a credential-stuffing attack in progress "
    "(severity=sev1, type=incident). Time matters — the attack is "
    "ongoing and 47 users are already locked out.\n\n"
    "**The codebase you are responding to ALREADY EXISTS in the "
    "working tree.** This is a real auth service — call `git_status` "
    "to see what's there, `read_file` to read it. Key files:\n"
    "  src/auth/service.py — AuthService.login / logout / get_session\n"
    "  src/auth/endpoints.py — /auth/login, /auth/logout, /auth/me\n"
    "  src/auth/middleware.py — Bearer-token session dependency\n"
    "  src/auth/models.py — User / Session / FailedAttempt\n"
    "  src/auth/passwords.py — bcrypt hash + verify\n"
    "  tests/test_auth.py — baseline coverage (no rate-limit tests)\n\n"
    "The codebase explicitly notes (in src/auth/__init__.py docstring "
    "and in #ENG-471 comments) that rate limiting and lockout policy "
    "are deferred-but-known gaps. The credential-stuffing attack is "
    "exploiting exactly those gaps. Your job is to fill them.\n\n"
    "- Queen: rule on immediate mitigation. Rate-limit shape (per IP? "
    "  per email? both?), lockout-policy adjustment, breach-disclosure "
    "  obligations if any credentials succeeded.\n"
    "- Cat: is the existing architectural surface intact? Read service.py "
    "  and middleware.py first; confirm/refute that the proposed "
    "  mitigation composes cleanly. Silence is fine if architecture "
    "  isn't implicated.\n"
    "- Tweedles: ship the mitigation as a clean DIFF against the "
    "  existing code. Add new files (e.g., src/auth/rate_limit.py) "
    "  AND modify existing ones where appropriate. Use write_file. "
    "  Extend tests/test_auth.py with the new coverage.\n"
    "- Hatter: test scenarios for the recurrence class — what should "
    "  monitoring catch next time? What test_scenarios extend "
    "  tests/test_auth.py to lock in the new behavior?\n"
    "- Caterpillar: review the shipped mitigation via git_diff HEAD — "
    "  the seed is the initial commit; the team's diff is everything "
    "  after.\n\n"
    "Don't wait for full architectural consensus before shipping the "
    "immediate stop. The Pair Protocol §V says contracts can be "
    "half-formed and locked through negotiation — apply that to the "
    "mitigation. Speed > perfection here."
)


async def main(project_root: Path) -> int:
    # Pre-seed the auth service into project_root and commit it as the
    # initial git state — the team responds to a real codebase, not an
    # empty directory. After this, `git_diff HEAD` shows ONLY the
    # team's changes; Caterpillar's review reads the diff cleanly.
    #
    # We do this BEFORE Runner.make_full_cast so the runner's
    # _ensure_git_repo sees .git already exists and skips its own
    # init+commit (it's idempotent on that check).
    seed_dir = _locate_seed_dir()
    print(f"Pre-seed:      {seed_dir} → {project_root}")
    shutil.copytree(seed_dir, project_root, dirs_exist_ok=True)
    _commit_seed_baseline(project_root)

    runner = await Runner.make_full_cast(
        project_root,
        budget_dollars=3.00,
        timeout_seconds=480.0,  # 8 minutes per T37 acceptance
        # 60s quiescence carries the T36 workaround pending the big
        # Dodo orchestration rework (roadmap 29497820). Late-publish
        # stop-gap (commit 04a73e2) makes any leaked deliberation
        # visible via runner.lost_utterances() at teardown.
        quiescence_seconds=60.0,
    )

    print("=" * 78)
    print("T37 SECURITY RECOVERY SHOWCASE — credential-stuffing incident")
    print("=" * 78)
    print(f"Project root:  {project_root}")
    print("Roster:        full cast (Queen, Dormouse, Cat, Tweedles, Hatter, Caterpillar, Alice, Rabbit, Dodo)")
    print("Budget cap:    $3.00 hard")
    print("Timeout:       480s (8min, T37 acceptance)")
    print("Quiescence:    60s")
    print()

    artifact_counts: dict[str, int] = defaultdict(int)
    speech_act_counts: dict[str, int] = defaultdict(int)
    queen_critical_rulings = 0
    tweedle_implementations = 0
    caterpillar_reviews = 0
    hatter_test_scenarios = 0
    start = time.monotonic()
    exit_code = 0

    # Construct the Dormouse observation utterance — the scenario primer.
    # Per T37 spec, this is published as a fresh utterance (not a seed)
    # so Queen's `always(OBSERVATION, condition=incident_words)` rule
    # fires on it. The body contains 'incident' and 'spike' which trip
    # the Queen's incident_words filter.
    dormouse_identity = AgentIdentity(
        name="dormouse", constitution_version="0.1"
    )
    incident_artifact = Artifact(
        kind="observation",
        payload={
            "title": INCIDENT_OBSERVATION_PAYLOAD.title,
            "type": INCIDENT_OBSERVATION_PAYLOAD.type.value,
            "severity": INCIDENT_OBSERVATION_PAYLOAD.severity.value,
            "symptom": INCIDENT_OBSERVATION_PAYLOAD.symptom,
            "affected_scope": INCIDENT_OBSERVATION_PAYLOAD.affected_scope,
            "evidence": INCIDENT_OBSERVATION_PAYLOAD.evidence,
            "probable_domain": INCIDENT_OBSERVATION_PAYLOAD.probable_domain,
            "routed_to": INCIDENT_OBSERVATION_PAYLOAD.routed_to,
        },
    )
    incident_utterance = Utterance(
        thread_id="incident-response",
        speaker=dormouse_identity,
        addressed_to="caucus",
        speech_act=SpeechAct.OBSERVATION,
        content=UtteranceContent(body=INCIDENT_BODY, artifacts=[incident_artifact]),
    )

    try:
        await runner.setup()
        await runner.convene(
            thread_id="incident-response",
            goal="contain the credential-stuffing attack and ship a code mitigation",
            roster=[
                "alice",
                "cheshire_cat",
                "white_rabbit",
                "mad_hatter",
                "caterpillar",
                "queen_of_hearts",
                "dormouse",
                "tweedledee",
                "tweedledum",
            ],
            seed_utterances=[incident_utterance],
            convenor_directive=CONVENOR_DIRECTIVE,
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
                    severity = artifact.payload.get("severity", "")
                    sev_s = f" [severity={severity}]" if severity else ""
                    print(f"{'':<29s}↳ {artifact.kind}: {title}{sev_s}")
                    # Acceptance-counter updates
                    if (
                        artifact.kind == "ruling"
                        and severity == "critical"
                        and u.speaker.name == "queen_of_hearts"
                    ):
                        queen_critical_rulings += 1
                    elif artifact.kind == "implementation" and u.speaker.name in (
                        "tweedledee",
                        "tweedledum",
                    ):
                        tweedle_implementations += 1
                    elif artifact.kind == "review" and u.speaker.name == "caterpillar":
                        caterpillar_reviews += 1
                    elif artifact.kind == "test_scenario" and u.speaker.name == "mad_hatter":
                        hatter_test_scenarios += 1
                sys.stdout.flush()
            elif event.kind == "state":
                change = event.payload["change"]
                print(
                    f"[t={event.elapsed:6.2f}s] {'<thread_monitor>':<18s} "
                    f"{change.from_state.value} → {change.to_state.value}"
                )
            elif event.kind == "complete":
                print(f"[t={event.elapsed:6.2f}s] <complete>           thread settled")
                break
            elif event.kind == "timeout":
                print(f"[t={event.elapsed:6.2f}s] <timeout>            480s exceeded")
                exit_code = 1
                break
            elif event.kind == "budget_exceeded":
                cost = event.payload["cost"]
                print(f"[t={event.elapsed:6.2f}s] <budget>             EXCEEDED ${cost:.2f}")
                break
    finally:
        elapsed_total = time.monotonic() - start
        await runner.teardown()

        print()
        print("=" * 78)
        print("T37 ACCEPTANCE SUMMARY")
        print("=" * 78)
        print(f"Elapsed:       {elapsed_total:.1f}s  (limit: 480s)")
        print(f"Total cost:    ${runner.total_cost:.4f}  (cap: $3.00)")
        print(f"LLM calls:     {runner.telemetry.call_count}")
        print()
        print("Acceptance criteria:")
        print(f"  [{'PASS' if queen_critical_rulings >= 1 else 'FAIL'}] Queen ≥1 critical-severity ruling   (got {queen_critical_rulings})")
        print(f"  [{'PASS' if tweedle_implementations >= 1 else 'FAIL'}] Tweedles ≥1 implementation           (got {tweedle_implementations})")
        print(f"  [{'PASS' if caterpillar_reviews >= 1 else 'FAIL'}] Caterpillar ≥1 review                (got {caterpillar_reviews})")
        print(f"  [{'PASS' if hatter_test_scenarios >= 1 else 'FAIL'}] Hatter ≥1 test_scenario              (got {hatter_test_scenarios})")
        print(f"  [{'PASS' if elapsed_total <= 480 else 'FAIL'}] Within 8min                          ({elapsed_total:.1f}s)")
        print(f"  [{'PASS' if runner.total_cost < 3.00 else 'FAIL'}] Under $3 cost                        (${runner.total_cost:.4f})")
        print()
        print("Speech acts:")
        for act, count in sorted(speech_act_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {act:18s} {count}")
        print()
        print("Artifacts shipped:")
        for kind, count in sorted(artifact_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {kind:18s} {count}")
        print()
        print("Files on disk under project_root (excluding .git, .wonderland, run.log):")
        any_files = False
        for f in sorted(project_root.rglob("*")):
            if (
                f.is_file()
                and ".git" not in f.parts
                and ".wonderland" not in f.parts
                and f.name not in ("run.log", ".gitignore")
            ):
                rel = f.relative_to(project_root)
                size = f.stat().st_size
                print(f"  {rel} ({size} bytes)")
                any_files = True
        if not any_files:
            print("  (no source files shipped — write_file was never called by Tweedles)")
        print()
        lost = runner.lost_utterances()
        if lost:
            print(f"Late-publish suppressed utterances: {len(lost)}")
            for u in lost:
                print(f"  {u.speaker.name} {u.speech_act.value} → {u.thread_id}")
        else:
            print("Late-publish: none — every deliberation finished within the meeting boundary.")

    return exit_code


if __name__ == "__main__":
    project_root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp())
    project_root.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(KeyboardInterrupt):
        sys.exit(asyncio.run(main(project_root)))
