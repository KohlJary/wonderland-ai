#!/usr/bin/env python3
"""scripts/annotate_transcript.py — produce a structured analysis stub
from a captured Wonderland showcase run.

Per WONDERLAND_SPEC §11 / gameplan T39: each showcase's transcript is
the artifact a reader needs to evaluate the thesis. Manual writeups
work for low N; this tool extracts the structural sections so the
human + Daedalus only have to add interpretation.

Usage:
    python scripts/annotate_transcript.py <run-log> [--project-root <dir>] [--out <md>]

Where:
- <run-log> is the captured stdout/stderr of a showcase script (the
  bus event lines, late-publish notices, parse errors, etc.).
- --project-root points at the showcase's project_root (the dir that
  has .wonderland/). Defaults to the run-log's parent if not given.
- --out is where to write the markdown stub. Defaults to stdout.

Sections produced:
- Headline numbers (cost, time, calls)
- Per-meeting breakdown (elapsed, calls, cost, artifacts, outcome)
- Speech-act distribution
- Per-agent token usage + cost
- Artifact summary (counts by registry)
- Thread-state log
- Late-publish + parse-error catalog
- Auto-detected patterns (signature heuristics)
- Code shipped (when project_root has a git repo with team commits)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

UTTERANCE_RE = re.compile(
    r"^\s*M(\d+)\[t=\s*([\d.]+)s\]\s+(\S+)\s+(\S+)\s+→\S+\s+(.*)$"
)
ARTIFACT_RE = re.compile(
    r"^\s*M\d+\s+↳\s+(\w+):\s+(.+?)(?:\s+\[(.+)\])?\s*$"
)
STATE_RE = re.compile(
    r"^\s*M(\d+)\[t=\s*([\d.]+)s\]\s+<thread_monitor>\s+(\w+)\s+→\s+(\w+)\s*$"
)
MEETING_HEADER_RE = re.compile(r"^MEETING M(\d+):\s+(.*)$")
MEETING_END_RE = re.compile(r"^\s*──\s+M(\d+)\s+END\s+──\s+outcome=(\w+)\s*$")
MEETING_STATS_RE = re.compile(
    r"^\s*elapsed:\s+([\d.]+)s|"
    r"^\s*this meeting:\s+(\d+) calls,\s+\$([\d.]+)|"
    r"^\s*artifacts:\s+(\d+)(?:\s+\((.*?)\))?"
)
LATE_PUBLISH_RE = re.compile(
    r"^\[late-publish\]\s+(\S+)\s+→\s+thread\s+'(\S+)'.*?—\s+suppressing\s+(\w+):\s+(.*)$"
)
PARSE_ERROR_RE = re.compile(
    r"^\[(\S+)\]\s+deliberate\(\)\s+raised\s+(\w+):\s+(.+?)\s+—\s+treating as silence\s*$"
)
TOTAL_ELAPSED_RE = re.compile(r"^Total elapsed:\s+([\d.]+)s")
TOTAL_COST_RE = re.compile(r"^Total cost:\s+\$([\d.]+)")
TOTAL_CALLS_RE = re.compile(r"^Total LLM calls:\s+(\d+)")


@dataclass
class Utterance:
    meeting: int
    elapsed: float
    speaker: str
    speech_act: str
    snippet: str


@dataclass
class StateTransition:
    meeting: int
    elapsed: float
    from_state: str
    to_state: str


@dataclass
class MeetingSummary:
    number: int
    title: str = ""
    outcome: str = ""
    elapsed_s: float = 0.0
    calls: int = 0
    cost: float = 0.0
    artifacts: int = 0
    artifact_breakdown: str = ""


@dataclass
class LatePublish:
    speaker: str
    thread: str
    speech_act: str
    snippet: str


@dataclass
class ParseError:
    speaker: str
    error_type: str
    detail: str


@dataclass
class ParsedRun:
    utterances: list[Utterance] = field(default_factory=list)
    transitions: list[StateTransition] = field(default_factory=list)
    meetings: dict[int, MeetingSummary] = field(default_factory=dict)
    late_publishes: list[LatePublish] = field(default_factory=list)
    parse_errors: list[ParseError] = field(default_factory=list)
    total_elapsed: float = 0.0
    total_cost: float = 0.0
    total_calls: int = 0


def parse_run_log(path: Path) -> ParsedRun:
    run = ParsedRun()
    with path.open() as f:
        lines = f.readlines()

    current_meeting: int | None = None
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")

        if m := MEETING_HEADER_RE.match(line):
            current_meeting = int(m.group(1))
            run.meetings.setdefault(
                current_meeting, MeetingSummary(number=current_meeting)
            ).title = m.group(2).strip()
            continue

        if m := MEETING_END_RE.match(line):
            num = int(m.group(1))
            ms = run.meetings.setdefault(num, MeetingSummary(number=num))
            ms.outcome = m.group(2)
            # Look ahead a few lines for the stats block
            for follow in lines[i + 1 : i + 8]:
                follow = follow.rstrip("\n")
                if mm := re.match(r"^\s*elapsed:\s+([\d.]+)s", follow):
                    ms.elapsed_s = float(mm.group(1))
                elif mm := re.match(
                    r"^\s*this meeting:\s+(\d+) calls,\s+\$([\d.]+)", follow
                ):
                    ms.calls = int(mm.group(1))
                    ms.cost = float(mm.group(2))
                elif mm := re.match(r"^\s*artifacts:\s+(\d+)\s*(?:\((.*?)\))?", follow):
                    ms.artifacts = int(mm.group(1))
                    if mm.group(2):
                        ms.artifact_breakdown = mm.group(2)
            continue

        if m := UTTERANCE_RE.match(line):
            run.utterances.append(
                Utterance(
                    meeting=int(m.group(1)),
                    elapsed=float(m.group(2)),
                    speaker=m.group(3),
                    speech_act=m.group(4),
                    snippet=m.group(5),
                )
            )
            continue

        if m := STATE_RE.match(line):
            run.transitions.append(
                StateTransition(
                    meeting=int(m.group(1)),
                    elapsed=float(m.group(2)),
                    from_state=m.group(3),
                    to_state=m.group(4),
                )
            )
            continue

        if m := LATE_PUBLISH_RE.match(line):
            run.late_publishes.append(
                LatePublish(
                    speaker=m.group(1),
                    thread=m.group(2),
                    speech_act=m.group(3),
                    snippet=m.group(4)[:120],
                )
            )
            continue

        if m := PARSE_ERROR_RE.match(line):
            run.parse_errors.append(
                ParseError(
                    speaker=m.group(1),
                    error_type=m.group(2),
                    detail=m.group(3)[:200],
                )
            )
            continue

        if m := TOTAL_ELAPSED_RE.match(line):
            run.total_elapsed = float(m.group(1))
        elif m := TOTAL_COST_RE.match(line):
            run.total_cost = float(m.group(1))
        elif m := TOTAL_CALLS_RE.match(line):
            run.total_calls = int(m.group(1))

    return run


# ---------------------------------------------------------------------------
# Loaders for sidecar data
# ---------------------------------------------------------------------------


def load_telemetry(project_root: Path | None) -> dict:
    if project_root is None:
        return {}
    tele_dir = project_root / ".wonderland" / "telemetry"
    if not tele_dir.is_dir():
        return {}
    runs = sorted(tele_dir.glob("run-*.json"))
    if not runs:
        return {}
    with runs[-1].open() as f:
        return json.load(f)


def count_artifacts(project_root: Path | None) -> dict[str, int]:
    if project_root is None:
        return {}
    wonderland = project_root / ".wonderland"
    if not wonderland.is_dir():
        return {}
    counts: dict[str, int] = {}
    for sub in wonderland.iterdir():
        if not sub.is_dir() or sub.name in ("memory", "telemetry"):
            continue
        files = list(sub.glob("*.md"))
        if files:
            counts[sub.name] = len(files)
    return counts


def code_shipped_diffstat(project_root: Path | None) -> str | None:
    """If the project_root is a git repo with a team commit on top of a
    seed, return the diff --stat between HEAD~1 and HEAD. Else None."""
    if project_root is None or not (project_root / ".git").is_dir():
        return None
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "-2"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if log.returncode != 0 or len(log.stdout.strip().splitlines()) < 2:
            return None
        diff = subprocess.run(
            ["git", "diff", "--stat", "HEAD~1", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return diff.stdout.strip() if diff.returncode == 0 else None
    except (subprocess.SubprocessError, OSError):
        return None


# ---------------------------------------------------------------------------
# Pattern detection
# ---------------------------------------------------------------------------


def detect_patterns(run: ParsedRun, telemetry: dict) -> list[str]:
    """Heuristic signatures from prior analyses. Each returns a one-line
    finding when triggered. Conservative — false positives are noisier
    than false negatives in an analysis stub."""
    findings: list[str] = []

    # Polite-deadlock: many turns total but no terminal artifacts (impl/review)
    if len(run.utterances) > 30:
        meaty_acts = {"implementation", "review", "ticket", "adr", "story", "ruling"}
        meaty = [u for u in run.utterances if u.speech_act in meaty_acts]
        if len(meaty) < len(run.utterances) * 0.15:
            findings.append(
                f"**Polite-deadlock signature:** {len(run.utterances)} utterances, "
                f"only {len(meaty)} carried terminal artifacts "
                f"({100 * len(meaty) / len(run.utterances):.0f}% — under 15% threshold). "
                "The team may be agreeing without shipping."
            )

    # Late-publish: any non-zero is worth surfacing
    if run.late_publishes:
        findings.append(
            f"**Late-publish events:** {len(run.late_publishes)} utterance(s) suppressed for "
            f"landing on already-COMPLETE threads. See catalog below; check whether "
            f"any were load-bearing artifacts vs ancillary commentary."
        )

    # Parse errors: any non-zero is worth surfacing
    if run.parse_errors:
        findings.append(
            f"**Parse-error turns lost:** {len(run.parse_errors)} deliberate() "
            f"call(s) raised *ResponseParseError and were treated as silence. "
            "Worth checking whether the lost work was substantive."
        )

    # Cat-cache-miss signature: cat with low cache-read ratio
    per_agent = telemetry.get("per_agent", {})
    cat = per_agent.get("cheshire_cat", {})
    if cat:
        read = cat.get("cache_read_input_tokens", 0)
        write = cat.get("cache_creation_input_tokens", 0)
        total = read + write + cat.get("input_tokens", 0)
        if total > 5000 and read < total * 0.3:
            findings.append(
                f"**Cat-cache-miss signature:** Cheshire Cat cache-read ratio "
                f"is {100 * read / total:.0f}% (under 30% threshold). "
                "Cache may not be priming correctly for this agent — see analyses 005/006."
            )

    # Sycophancy / agreement signature: many short concurrence-style speech acts
    deferences = sum(1 for u in run.utterances if u.speech_act == "deference")
    if deferences > 5 and deferences > len(run.utterances) * 0.2:
        findings.append(
            f"**Deference-heavy signature:** {deferences} `deference` utterances "
            f"({100 * deferences / len(run.utterances):.0f}%). May indicate sycophancy "
            "or unbalanced authority structure."
        )

    return findings


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render(
    run: ParsedRun,
    telemetry: dict,
    artifact_counts: dict[str, int],
    diffstat: str | None,
) -> str:
    out: list[str] = []

    # Headline
    out.append("# Analysis stub (auto-generated)\n")
    out.append("> Generated by `scripts/annotate_transcript.py`. Add interpretation, then publish.\n")
    out.append("## Headline numbers\n")
    out.append(f"- **Total elapsed:** {run.total_elapsed:.1f}s")
    out.append(f"- **Total cost:** ${run.total_cost:.4f}")
    out.append(f"- **Total LLM calls:** {run.total_calls}")
    out.append(f"- **Utterances on bus:** {len(run.utterances)}")
    out.append(f"- **Late-publish events:** {len(run.late_publishes)}")
    out.append(f"- **Parse-error turns:** {len(run.parse_errors)}\n")

    # Per-meeting
    if run.meetings:
        out.append("## Per-meeting breakdown\n")
        out.append("| # | Title | Outcome | Elapsed | Calls | Cost | Artifacts |")
        out.append("|---|---|---|---|---|---|---|")
        for num in sorted(run.meetings):
            ms = run.meetings[num]
            artifact_str = str(ms.artifacts)
            if ms.artifact_breakdown:
                artifact_str += f" ({ms.artifact_breakdown})"
            out.append(
                f"| M{ms.number} | {ms.title or '?'} | {ms.outcome or '?'} | "
                f"{ms.elapsed_s:.1f}s | {ms.calls} | ${ms.cost:.4f} | {artifact_str} |"
            )
        out.append("")

    # Speech-act distribution
    if run.utterances:
        out.append("## Speech-act distribution\n")
        sa_counts = Counter(u.speech_act for u in run.utterances)
        out.append("| Speech act | Count | Share |")
        out.append("|---|---|---|")
        total = len(run.utterances)
        for sa, n in sa_counts.most_common():
            out.append(f"| {sa} | {n} | {100 * n / total:.0f}% |")
        out.append("")

    # Per-agent breakdown — combine bus utterance counts and telemetry $ if available
    out.append("## Per-agent breakdown\n")
    per_agent_calls = Counter(u.speaker for u in run.utterances)
    per_agent_tele = telemetry.get("per_agent", {})
    if per_agent_calls or per_agent_tele:
        out.append("| Agent | Utterances | LLM calls | Input | Output | Cache read | Cost |")
        out.append("|---|---|---|---|---|---|---|")
        agents = sorted(set(per_agent_calls) | set(per_agent_tele))
        for agent in agents:
            t = per_agent_tele.get(agent, {})
            out.append(
                f"| {agent} | {per_agent_calls.get(agent, 0)} | "
                f"{t.get('calls', '?')} | {t.get('input_tokens', '?')} | "
                f"{t.get('output_tokens', '?')} | {t.get('cache_read_input_tokens', '?')} | "
                f"${t.get('cost', 0):.4f} |"
            )
        out.append("")

    # Artifact summary
    if artifact_counts:
        out.append("## Artifacts persisted\n")
        out.append("| Registry | Files |")
        out.append("|---|---|")
        for kind, n in sorted(artifact_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            out.append(f"| {kind}/ | {n} |")
        out.append("")

    # Thread-state log
    if run.transitions:
        out.append("## Thread-state log\n")
        out.append("| t | M | from → to |")
        out.append("|---|---|---|")
        for t in run.transitions:
            out.append(f"| {t.elapsed:.1f}s | M{t.meeting} | {t.from_state} → {t.to_state} |")
        out.append("")

    # Late-publish catalog
    if run.late_publishes:
        out.append("## Late-publish catalog\n")
        for lp in run.late_publishes:
            out.append(
                f"- `{lp.speaker}` → `{lp.thread}` (already COMPLETE), "
                f"suppressed `{lp.speech_act}`: \"{lp.snippet}\""
            )
        out.append("")

    # Parse-error catalog
    if run.parse_errors:
        out.append("## Parse-error catalog\n")
        for pe in run.parse_errors:
            out.append(f"- `{pe.speaker}`: **{pe.error_type}** — {pe.detail}")
        out.append("")

    # Code shipped
    if diffstat:
        out.append("## Code shipped (HEAD~1 → HEAD)\n")
        out.append("```")
        out.append(diffstat)
        out.append("```\n")

    # Auto-detected patterns
    patterns = detect_patterns(run, telemetry)
    out.append("## Auto-detected patterns\n")
    if patterns:
        for p in patterns:
            out.append(f"- {p}")
    else:
        out.append("_No known signatures triggered._")
    out.append("")

    # Stub for human interpretation
    out.append("## Interpretation (fill in)\n")
    out.append("- **Headline finding:** _(what the run actually shows that matters)_")
    out.append("- **What worked:** _(specific wins)_")
    out.append("- **What didn't:** _(specific failures + their cause)_")
    out.append("- **What's next:** _(roadmap items, follow-up runs)_")
    out.append("")

    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    p = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    p.add_argument("log", type=Path, help="captured run log (stdout/stderr of showcase)")
    p.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="project_root that has .wonderland/ (defaults to log's parent)",
    )
    p.add_argument(
        "--out", type=Path, default=None, help="output markdown file (default: stdout)"
    )
    args = p.parse_args()

    if not args.log.is_file():
        p.error(f"log not found: {args.log}")

    project_root = args.project_root or args.log.parent
    if not (project_root / ".wonderland").is_dir():
        # If project_root doesn't have .wonderland, telemetry/artifacts are empty
        # but parsing the log still works.
        project_root = None  # type: ignore[assignment]

    run = parse_run_log(args.log)
    telemetry = load_telemetry(project_root)
    artifacts = count_artifacts(project_root)
    diffstat = code_shipped_diffstat(project_root)

    md = render(run, telemetry, artifacts, diffstat)

    if args.out:
        args.out.write_text(md)
        print(f"wrote {len(md)} chars to {args.out}")
    else:
        print(md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
