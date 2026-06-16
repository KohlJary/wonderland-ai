"""Tools — read/write/list/grep primitives the Tweedles can use to ship code.

Per the P6.T36 prep tool-integration decision (after analysis 014's
cross-meeting composition validated that the Tweedles ship Contract
Notes that imply real implementation work): give the Tweedles a small
sandbox of file primitives so their `implementation` artifacts are
backed by actual code on disk, not just markdown describing what would
ship.

Scope decisions (deliberately minimal — see analysis 014's tooling
follow-up):

- **read_file**, **write_file**, **list_files**, **grep**: covers
  shipping basic code. The Tweedles need to know what's there
  (list/grep) before writing more (read/write).
- **No run_command**: executing arbitrary code is a separate trust
  boundary. Defer until a showcase explicitly needs it.

Path safety: every operation resolves the requested path relative to
``project_root`` and rejects anything that escapes (``..`` symlinks,
absolute paths outside the root, etc.). The Tweedles can't reach
outside their project sandbox even if the LLM tries — the sandbox is
the trust boundary, the Tweedles are inside it.

Anthropic tool-use schema lives next to the implementations so adding
a new tool is one place to edit. ``Tools.tool_definitions()`` returns
the list to pass as ``tools=[...]`` to ``messages.create``.
"""

from __future__ import annotations

import json
import re
import subprocess
import shutil
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Hard cap on file size to avoid pulling massive blobs into the LLM context.
# Most source files are well under this; binaries or large assets get truncated
# with a clear marker so the LLM can decide what to do.
MAX_READ_BYTES = 64 * 1024  # 64 KiB

# Cap for `run_tests` output. Tighter than MAX_READ_BYTES — pytest
# output for large failing suites can be tens of KB and would dominate
# the LLM's context window. The compact summary + truncated failure
# detail is what's load-bearing for the Tweedles' red→green loop.
MAX_TEST_OUTPUT_BYTES = 4 * 1024  # 4 KiB ≈ ~1k tokens

# Default per-call wall-clock cap for `run_tests`. Long enough for a
# real test suite, short enough that a hung test doesn't burn the
# meeting's wall-clock budget.
DEFAULT_TEST_TIMEOUT_SECONDS = 60.0

# Cap on snippet length passed to `exec_smoke_probe`. Probes that need
# more than 16 KiB are doing something other than smoke-testing a code
# path — they should be a proper test in `tests/` instead.
MAX_PROBE_SNIPPET_BYTES = 16 * 1024

# Cap on `exec_smoke_probe` output. Same shape rationale as
# MAX_TEST_OUTPUT_BYTES — a stack trace + a few lines of stdout is the
# load-bearing signal; an exploded REPL dump dominates the LLM context.
MAX_PROBE_OUTPUT_BYTES = 4 * 1024

# Default wall-clock cap for `exec_smoke_probe`. Tighter than
# DEFAULT_TEST_TIMEOUT_SECONDS — probes exercise a single code path,
# not the full suite, so 30s is generous.
DEFAULT_PROBE_TIMEOUT_SECONDS = 30.0

# Hard cap on the number of grep results to avoid context-flood.
MAX_GREP_HITS = 100

# Hard cap on the number of list_files results.
MAX_LIST_ENTRIES = 200


# ---------------------------------------------------------------------
# Tool-call observability (P10 / T66 / roadmap 33e29f5c)
# ---------------------------------------------------------------------
# Per analyses 032 + 035: Tweedles are 78.8% of total run cost with
# ~13-15 LLM calls per deliberation, almost all of those being
# write_file / read_file / run_tests tool loops. Surfacing each tool
# call as a timestamped event lets post-run analysis quantify exactly
# which tool calls drive cost (vs inferring from per-agent telemetry).
# Also unblocks the diff-tool A/B test (T67/T68): we can measure the
# input-token compression directly instead of estimating.


@dataclass(frozen=True)
class ToolCallEvent:
    """One tool invocation observed at the dispatch layer.

    Captures the timing, the agent who called it, and the input/output
    sizes — enough to answer 'what fraction of Tweedle cost is
    write_file?' post-run without re-reading the bus log. Sensitive
    content (write_file body, read_file result) is summarized by
    byte size, not stored verbatim — full content lives in the
    working tree + utterance bus already.
    """

    timestamp: datetime
    tool_name: str
    agent_id: str | None
    """The agent who invoked the tool, when known. The phased
    orchestrator and most agent-driven calls populate this; synthetic
    or test-harness calls leave it None."""
    args_summary: dict[str, Any]
    """Sanitized arguments — small fields verbatim (path, pattern,
    ignore_case), large fields summarized as ``{kind}_bytes`` (the
    ``content`` arg of write_file becomes ``content_bytes``)."""
    input_bytes: int
    """Total bytes of all input args combined. Catches the cost of a
    write_file call that re-sends a 10K-line file just to flip one
    line."""
    elapsed_ms: float
    """Wall-clock for the dispatch. Includes any subprocess overhead
    (run_tests' pytest invocation, git_status' git invocation)."""
    result_bytes: int
    """Bytes of the returned string. None on error."""
    error: str | None = None
    """ToolError message if the dispatch raised, else None."""
    file_size_after_bytes: int | None = None
    """For diff-write operations (str_replace, insert): the byte size
    of the file *after* the patch. Lets post-run analysis compute
    bytes saved vs a hypothetical full ``write_file``: a write_file
    of the patched file would have consumed
    ``file_size_after_bytes`` of input; the diff op consumed
    ``input_bytes``. Savings = file_size_after_bytes - input_bytes.
    None for read-only ops + write_file (where input_bytes already
    captures the full file size, no comparison needed)."""


ToolCallWriter = Callable[[ToolCallEvent], None]
"""Callback signature for tool-call observers. Synchronous because
``Tools.execute`` is itself sync — no async surface to plumb through
the dispatch path. The default writer (jsonl_tool_call_writer) does
a per-event open-append-close for crash safety."""


def _serialize_tool_call_event(event: ToolCallEvent) -> dict[str, Any]:
    """JSON-friendly form of a ToolCallEvent."""
    payload = asdict(event)
    if isinstance(event.timestamp, datetime):
        payload["timestamp"] = event.timestamp.isoformat()
    return payload


def _deserialize_tool_call_event(payload: dict[str, Any]) -> ToolCallEvent:
    """Round-trip a tool-call event from its on-disk dict form."""
    if isinstance(payload.get("timestamp"), str):
        payload["timestamp"] = datetime.fromisoformat(payload["timestamp"])
    return ToolCallEvent(**payload)


def jsonl_tool_call_writer(path: Path) -> ToolCallWriter:
    """Build a writer that appends one JSON line per tool call to
    ``path``. Parent dir is created if missing. Same shape as the
    phase-events writer for consistency — open-append-close per
    event so a crash mid-meeting still leaves a partial-but-readable
    log."""
    path.parent.mkdir(parents=True, exist_ok=True)

    def _write(event: ToolCallEvent) -> None:
        line = json.dumps(_serialize_tool_call_event(event)) + "\n"
        with path.open("a") as f:
            f.write(line)

    return _write


def read_tool_calls(path: Path) -> list[ToolCallEvent]:
    """Read a tool-calls.jsonl file and return events in write
    order. Empty list for missing files (older snapshots predate
    T66)."""
    if not path.is_file():
        return []
    events: list[ToolCallEvent] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(_deserialize_tool_call_event(json.loads(line)))
    return events


def _summarize_tool_args(
    tool_name: str, tool_input: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    """Build a sanitized args summary + total input-byte count.

    Small string fields (path, pattern, directory) round-trip
    verbatim because they're useful for post-run analysis (e.g.
    'how often did Tweedledum write_file to src/api.py'). Large
    string fields (content for write_file) are replaced with a
    byte-count entry so the JSONL stays small. Boolean / int
    fields round-trip verbatim.
    """
    summary: dict[str, Any] = {}
    total_bytes = 0
    for key, value in tool_input.items():
        if value is None:
            summary[key] = None
            continue
        if isinstance(value, str):
            byte_size = len(value.encode("utf-8"))
            total_bytes += byte_size
            # Keep small fields verbatim; summarize large blobs by
            # size. The "content" field of write_file is the load-
            # bearing case here — it can be many KB and would bloat
            # the JSONL unhelpfully.
            if key == "content" or byte_size > 256:
                summary[f"{key}_bytes"] = byte_size
            else:
                summary[key] = value
        elif isinstance(value, (int, float, bool)):
            summary[key] = value
        elif isinstance(value, list):
            # paths=[...] in run_tests gets kept verbatim; small.
            summary[key] = value
            for item in value:
                if isinstance(item, str):
                    total_bytes += len(item.encode("utf-8"))
        else:
            summary[key] = repr(value)
    return summary, total_bytes


@dataclass(frozen=True)
class ToolError(Exception):
    """Tool execution failed (sandbox violation, missing path, encoding error).

    Raised so the Tweedle's tool-use loop can convert the error into a
    structured tool_result with ``is_error=True`` for the LLM to read
    and recover from.
    """

    message: str

    def __str__(self) -> str:
        return self.message


class Tools:
    """File primitives sandboxed to a project root.

    Construct once per Runner. Pass to the Tweedles' constructor; their
    ``deliberate()`` method runs the tool-use loop with these tools
    available.
    """

    def __init__(
        self,
        project_root: Path,
        on_tool_call: ToolCallWriter | None = None,
    ) -> None:
        self._root = project_root.resolve()
        # Tool-call observability hook (T66). When set, each
        # ``execute()`` invocation calls this with a ToolCallEvent
        # capturing timing + sizes + error. The runner installs a
        # default writer pointing at .wonderland/tool-calls.jsonl;
        # tests can install their own writer to assert dispatch
        # behavior without disk I/O.
        self._on_tool_call = on_tool_call
        # Per-call metadata stash (T67). Diff-write methods
        # (str_replace, insert) write here before returning so
        # ``execute()`` can include file_size_after_bytes in the
        # observability event. Cleared at the start of each
        # execute() call.
        self._last_op_metadata: dict[str, Any] | None = None

    @property
    def project_root(self) -> Path:
        return self._root

    # ------------------------------------------------------------------ #
    # Path safety
    # ------------------------------------------------------------------ #

    def _resolve(self, requested: str) -> Path:
        """Resolve a path string relative to project_root; reject escapes.

        ``requested`` may be a relative path (interpreted from
        project_root) or an absolute path (must be inside project_root).
        Symlink resolution happens here so an in-tree symlink pointing
        out of the tree gets caught.
        """
        path = (
            (self._root / requested).resolve()
            if not Path(requested).is_absolute()
            else Path(requested).resolve()
        )
        # Use is_relative_to (Python 3.9+) for the sandbox check.
        if not path.is_relative_to(self._root):
            raise ToolError(f"path {requested!r} escapes project root {self._root}")
        return path

    def _check_delete_allowed(self, requested: str, full: Path) -> None:
        """T-ab12 (ccf5fdfe) — refuse agent-initiated DELETES on
        substrate-of-record paths under ``.wonderland/``.

        Observed failure: mvp-demo-rerun-A M2 design pass deleted
        the M1 milestone file, leaving the M1 design run with an
        empty milestone seed pool and the full-app-scope drift
        symptom. Deletion of substrate artifacts during a design/
        impl workflow is never the right semantic — agents that
        want to remove an artifact should emit a ``retract``
        speech_act (which is workflow-aware), not raw file-tool
        unlinks.

        Mutation (write_file / str_replace / insert) is still
        permitted: agents may legitimately need to amend a
        milestone's content (fix a typo in done-when, correct a
        consumes_requirements slug). The mutation path keeps the
        file on disk so the seed-loader and substrate guards still
        see the artifact; deletion would silently remove it.

        Deletion of source files (src/, tests/, frontend/) remains
        unaffected — that's the legitimate workflow for cleaning
        up implementation atoms.
        """
        try:
            rel = full.relative_to(self._root)
        except ValueError:
            return  # _resolve already raises on escapes
        rel_str = rel.as_posix()
        protected_prefixes = (
            ".wonderland/milestones",
            ".wonderland/requirements",
            ".wonderland/memory",
        )
        protected_files = (
            ".wonderland/project.yaml",
            ".wonderland/feature-states.jsonl",
            ".wonderland/ticket-states.jsonl",
            ".wonderland/phase-events.jsonl",
            ".wonderland/tool-calls.jsonl",
            ".wonderland/milestone-unlink.log",
        )
        if rel_str in protected_files:
            raise ToolError(
                f"refusing to delete substrate-of-record file "
                f"{requested!r}: this file is owned by the substrate "
                f"(project config / lifecycle state / audit log). "
                f"Deletion is not the right semantic here."
            )
        for prefix in protected_prefixes:
            if rel_str == prefix or rel_str.startswith(prefix + "/"):
                raise ToolError(
                    f"refusing to delete substrate-of-record path "
                    f"{requested!r}: artifacts under this directory "
                    f"are owned by a specific workflow (milestones → "
                    f"milestone-plan; requirements → discovery; "
                    f"memory → substrate). Use a ``retract`` "
                    f"speech_act instead of raw delete_file — "
                    f"retract is workflow-aware and reversible; "
                    f"file deletion is neither."
                )

    def _check_milestone_scope_allowed_read(
        self, requested: str, full: Path,
    ) -> None:
        """T-ab35 — refuse cross-milestone reads of stories/features/
        tickets during the scoping + composition phases of a milestone-
        scoped workflow.

        Observed failure: obol-260522 M4 design stalled across 4
        reruns even with empty memory + scoped framing because agents
        used ``read_file`` to navigate to M0/M2/M3 stories and
        features, then got drawn into cross-milestone coherence
        concerns instead of M4 feature composition. The substrate's
        memory + framing fixes cover the IMPLICIT context layer (what
        agents passively see); this guard closes the EXPLICIT context
        layer (what they actively pull via tools).

        Scope of the guard:
          - **Only when** an active milestone scope is set AND the
            current meeting id ends in ``scoping`` or ``composition``
            (the early design phases where no per-feature anchor
            exists yet). Later phases (decomposition, consolidation,
            architecture, contract-negotiation, implement, review,
            verify) iterate per-feature and self-scope via existing
            iteration filters (T-ab17/19/20).
          - **Only blocks** stories/features/tickets directories.
            ADRs (architecture/), milestones/, requirements/, contract-
            notes/, reviews/, rulings/ remain readable cross-scope —
            those are legitimate foundation-context lookups.
          - **Reads of the active milestone's own artifacts** are
            always allowed.
          - **Unattributable artifacts** (no parseable Milestone:
            field, or Sources: that resolves to nothing) stay
            readable — defensive default, similar to seeds_fallback.
        """
        from wonderland.telemetry import get_current_meeting_id
        try:
            from wonderland.workflow import get_active_milestone_scope
            scope = get_active_milestone_scope()
        except Exception:  # noqa: BLE001
            scope = None
        if scope is None:
            return  # no scope set → no constraint
        meeting_id = get_current_meeting_id() or ""
        # Phase detection via meeting id suffix. tdd-design meetings
        # have id ``scoping``, ``composition``, etc. Pipeline mode
        # prefixes with ``pipe.<feature>.``; endswith covers both.
        if not (
            meeting_id == "scoping"
            or meeting_id == "composition"
            or meeting_id.endswith(".scoping")
            or meeting_id.endswith(".composition")
        ):
            return  # outside the load-bearing phases → no constraint

        try:
            rel = full.resolve().relative_to(self._root.resolve())
        except (ValueError, OSError):
            return
        rel_str = str(rel).replace("\\", "/")
        wonderland_prefix = ".wonderland/"
        if not rel_str.startswith(wonderland_prefix):
            return  # source-tree reads aren't milestone-scoped
        artifact_kind: str | None = None
        for kind in ("stories", "features", "tickets"):
            if rel_str.startswith(f"{wonderland_prefix}{kind}/"):
                artifact_kind = kind
                break
        if artifact_kind is None:
            return  # not a scope-guarded artifact kind

        # Read the artifact's milestone attribution. Stories/features
        # carry the explicit field (T-ab7); tickets follow their
        # parent feature (T-ab33 ensures sources[0] is the feature).
        import re
        try:
            body = full.read_text(encoding="utf-8")
        except OSError:
            return  # let the actual read attempt produce the error
        artifact_milestone: str | None = None
        if artifact_kind in ("stories", "features"):
            m = re.search(r"^\*\*Milestone:\*\*\s*(.+?)$", body, re.MULTILINE)
            if m:
                val = m.group(1).strip()
                # Strip guid prefix: ``<guid>:<slug>`` → ``<slug>``
                artifact_milestone = (
                    val.split(":", 1)[1] if ":" in val else val
                )
        else:  # tickets
            m = re.search(r"^\*\*Sources:\*\*\s*(.+?)$", body, re.MULTILINE)
            if m:
                first_source = m.group(1).split(",")[0].strip()
                if ":" in first_source:
                    first_source = first_source.split(":", 1)[1]
                # Resolve first_source (feature slug) → its milestone
                from wonderland.feature import FeatureRegistry
                try:
                    feature_reg = FeatureRegistry(self._root)
                    feat_record = feature_reg.find_by_slug(first_source)
                    if feat_record is not None:
                        feat_body = feat_record.read()
                        fm = re.search(
                            r"^\*\*Milestone:\*\*\s*(.+?)$",
                            feat_body,
                            re.MULTILINE,
                        )
                        if fm:
                            val = fm.group(1).strip()
                            artifact_milestone = (
                                val.split(":", 1)[1] if ":" in val else val
                            )
                except Exception:  # noqa: BLE001
                    pass

        if artifact_milestone is None:
            return  # unattributable → defensive default, allow read
        if artifact_milestone == scope.slug:
            return  # in-scope read → allow

        # Cross-milestone read during scoping/composition → block.
        raise ToolError(
            f"refusing to read cross-milestone {artifact_kind[:-1]} "
            f"{requested!r} during {meeting_id} phase of milestone "
            f"``{scope.slug}``. This artifact attributes to "
            f"``{artifact_milestone}``, which is a sibling milestone — "
            f"reading it pulls cross-milestone concerns into your "
            f"current scope (obol-260522 M4 documented this drift). "
            f"Stay anchored on ``{scope.slug}``'s own "
            f"stories/features/tickets and the milestone-level "
            f"artifacts (ADRs, milestone files, requirements, "
            f"contract-notes, reviews) which remain readable "
            f"cross-scope. If you need this artifact for legitimate "
            f"foundation context, surface a ``concern`` rather than "
            f"pulling it directly."
        )

    def _artifact_milestone_or_none(self, full: Path) -> str | None:
        """T-ab46 helper: parse the ``**Milestone:**`` slug from an
        artifact path (story / feature). Tickets resolve via their
        sources[0] feature. Returns None when the file isn't an
        attributable artifact or when parsing fails — caller treats
        None as "leave visible" (defensive default mirroring T-ab35).
        """
        import re
        try:
            rel = full.resolve().relative_to(self._root.resolve())
        except (ValueError, OSError):
            return None
        rel_str = str(rel).replace("\\", "/")
        kind: str | None = None
        for k in ("stories", "features", "tickets"):
            if rel_str.startswith(f".wonderland/{k}/"):
                kind = k
                break
        if kind is None:
            return None
        try:
            body = full.read_text(encoding="utf-8")
        except OSError:
            return None
        if kind in ("stories", "features"):
            m = re.search(
                r"^\*\*Milestone:\*\*\s*(.+?)$", body, re.MULTILINE,
            )
            if m:
                val = m.group(1).strip()
                return val.split(":", 1)[1] if ":" in val else val
            return None
        # tickets — follow sources[0] → feature
        m = re.search(
            r"^\*\*Sources:\*\*\s*(.+?)$", body, re.MULTILINE,
        )
        if not m:
            return None
        first_source = m.group(1).split(",")[0].strip()
        if ":" in first_source:
            first_source = first_source.split(":", 1)[1]
        from wonderland.feature import FeatureRegistry
        try:
            feat_record = FeatureRegistry(self._root).find_by_slug(
                first_source
            )
            if feat_record is None:
                return None
            feat_body = feat_record.read()
            fm = re.search(
                r"^\*\*Milestone:\*\*\s*(.+?)$",
                feat_body,
                re.MULTILINE,
            )
            if fm:
                val = fm.group(1).strip()
                return val.split(":", 1)[1] if ":" in val else val
        except Exception:  # noqa: BLE001
            return None
        return None

    def _filter_cross_milestone_paths(
        self, paths: list[Path],
    ) -> list[Path]:
        """T-ab46 — drop cross-milestone artifact paths from a listing
        result when the active meeting is scoping/composition with an
        active milestone scope set.

        Same conditions as ``_check_milestone_scope_allowed_read``;
        same scope-detection contract. The difference is the response:
        ``read_file`` raises ToolError to refuse explicitly;
        ``list_files`` silently hides cross-milestone artifacts from
        the listing so agents don't even see they exist (the filename
        alone leaks the concept slug, which alice/cat then reason
        about as "already covered" and skip generating fresh stories).

        Paths that aren't under ``.wonderland/{stories,features,
        tickets}/`` pass through untouched. Paths whose artifact is
        unattributable (no Milestone: field, or sources don't resolve)
        also pass through — defensive default mirrors T-ab35.
        """
        from wonderland.telemetry import get_current_meeting_id
        try:
            from wonderland.workflow import get_active_milestone_scope
            scope = get_active_milestone_scope()
        except Exception:  # noqa: BLE001
            scope = None
        if scope is None:
            return paths
        meeting_id = get_current_meeting_id() or ""
        if not (
            meeting_id == "scoping"
            or meeting_id == "composition"
            or meeting_id.endswith(".scoping")
            or meeting_id.endswith(".composition")
        ):
            return paths

        kept: list[Path] = []
        for p in paths:
            artifact_milestone = self._artifact_milestone_or_none(p)
            if artifact_milestone is None:
                # Not a guarded artifact OR unattributable → visible.
                kept.append(p)
                continue
            if artifact_milestone == scope.slug:
                kept.append(p)
        return kept

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    def read_file(
        self,
        path: str,
        *,
        offset: int | None = None,
        limit: int | None = None,
    ) -> str:
        """Read a UTF-8 text file and return its contents.

        Optional line-range read via ``offset`` (1-indexed start line)
        and ``limit`` (number of lines to return). Reduces per-call
        context cost when the agent only needs a specific section —
        observed on obol-demo3 M7 where Tweedles re-read the same
        ~200-line files 40-58 times in a single thread, mostly to
        check small details. Line-range reads cut the per-call
        token spend on those by ~5-10x.

        Behavior:
          - No offset, no limit: full file (legacy behavior).
          - offset=N, no limit: read from line N to EOF.
          - offset=N, limit=K: read K lines starting at line N.
          - no offset, limit=K: read first K lines.

        Lines are returned with line-number prefixes when a range
        is requested (so the agent knows where in the file they are
        and can re-anchor on the same range later without re-reading
        the whole file). Full-file reads keep the legacy no-prefix
        format for back-compat.

        Files larger than ``MAX_READ_BYTES`` (full-file reads only)
        are truncated with a trailing ``[truncated: N more bytes]``
        marker. Binary files (UTF-8 decode errors) raise ToolError.

        Out-of-range offset / negative offset raise ToolError so the
        agent gets clear feedback rather than silent empty output.
        """
        full = self._resolve(path)
        if not full.exists():
            raise ToolError(f"file not found: {path}")
        if not full.is_file():
            raise ToolError(f"not a file: {path}")
        # T-ab35: scoping/composition phases of milestone-scoped runs
        # cannot read cross-milestone stories/features/tickets. Each
        # phase has its own context window; cross-milestone artifact
        # reads during scoping pull agents into "what about M0/M2/M3
        # coherence" rabbit-holes (obol-260522 M4: 4 reruns stalled).
        self._check_milestone_scope_allowed_read(path, full)
        try:
            data = full.read_bytes()
        except OSError as exc:
            raise ToolError(f"read failed for {path}: {exc}") from exc
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError(
                f"file {path} is not valid UTF-8 (cannot read as text): {exc}"
            ) from exc

        # Line-range path: when offset OR limit set, return a
        # numbered slice. Cheaper per-call than full file.
        if offset is not None or limit is not None:
            lines = text.splitlines(keepends=True)
            total = len(lines)
            start_idx = (offset - 1) if offset is not None else 0
            if start_idx < 0:
                raise ToolError(
                    f"offset must be >= 1 (got {offset})"
                )
            if start_idx >= total and total > 0:
                raise ToolError(
                    f"offset {offset} is past EOF "
                    f"({path} has {total} lines)"
                )
            if limit is not None and limit < 1:
                raise ToolError(
                    f"limit must be >= 1 (got {limit})"
                )
            end_idx = (
                start_idx + limit
                if limit is not None
                else total
            )
            end_idx = min(end_idx, total)
            slice_lines = lines[start_idx:end_idx]
            numbered = [
                f"{start_idx + i + 1:>5}\t{line}"
                for i, line in enumerate(slice_lines)
            ]
            result = "".join(numbered)
            if not result.endswith("\n"):
                result += "\n"
            footer = (
                f"\n[lines {start_idx + 1}-{end_idx} of {total} "
                f"in {path}]"
            )
            return result + footer

        # Full-file path (legacy): truncate at MAX_READ_BYTES.
        truncated_bytes = len(data) > MAX_READ_BYTES
        if truncated_bytes:
            try:
                text = data[:MAX_READ_BYTES].decode("utf-8")
            except UnicodeDecodeError:
                # Edge case: truncation cut a multi-byte char.
                text = data[:MAX_READ_BYTES].decode(
                    "utf-8", errors="ignore"
                )
            remaining = full.stat().st_size - MAX_READ_BYTES
            text += f"\n\n[truncated: {remaining} more bytes]"
        return text

    def write_file(self, path: str, content: str) -> str:
        """Write content to a file (creating parent directories as needed).

        Overwrites existing files. Returns a short acknowledgement so
        the LLM gets a useful tool_result.
        """
        full = self._resolve(path)
        if full.is_dir():
            raise ToolError(f"path is a directory, not a file: {path}")
        try:
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"write failed for {path}: {exc}") from exc
        return f"wrote {len(content)} chars to {path}"

    def delete_file(self, path: str) -> str:
        """Delete a file from the project tree.

        Sandboxed to project_root via _resolve; refuses directories.
        Useful for pruning duplicate artifacts (e.g. Rabbit dropping
        merged tickets during M3.5 consolidation, or Caterpillar
        dropping orphaned implementation files in M8 review).

        Idempotent on missing files: returns a "not found" message
        rather than raising, so an agent that wasn't sure whether
        the file existed doesn't have to pre-check with read_file.
        """
        full = self._resolve(path)
        self._check_delete_allowed(path, full)
        if full.is_dir():
            raise ToolError(
                f"path is a directory, not a file: {path}; "
                f"delete_file refuses directory deletes"
            )
        if not full.exists():
            return f"no file at {path} (already gone or never existed)"
        try:
            full.unlink()
        except OSError as exc:
            raise ToolError(
                f"delete failed for {path}: {exc}"
            ) from exc
        return f"deleted {path}"

    def str_replace(self, path: str, old: str, new: str) -> str:
        """Replace exactly one occurrence of ``old`` with ``new`` in
        ``path``. Token-cheap diff primitive (P10 / T67 / roadmap
        0858a936).

        Per analysis 032's estimate: a 250-line file iterated 4 times
        via full ``write_file`` costs ~1180 lines of input across 4
        calls; the same iteration via ``str_replace`` costs ~340 lines
        — roughly 3.5× compression on iterative file authoring.

        Validation is strict on purpose: ``old`` must match exactly
        once. Zero matches → ToolError (the LLM's anchor was wrong;
        worth re-reading and trying again rather than silently
        creating garbage). Multiple matches → ToolError (ambiguous;
        the LLM must include enough surrounding context to make the
        match unique). Empty ``old`` → ToolError (use ``insert``
        instead). Deletion is supported via ``new=""`` — strict
        match still applies.
        """
        if not old:
            raise ToolError(
                "str_replace: 'old' cannot be empty (use insert for "
                "additions, write_file for whole-file rewrites)"
            )
        full = self._resolve(path)
        if not full.exists():
            raise ToolError(f"file not found: {path}")
        if not full.is_file():
            raise ToolError(f"not a file: {path}")
        try:
            text = full.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError(
                f"file {path} is not valid UTF-8: {exc}"
            ) from exc
        match_count = text.count(old)
        if match_count == 0:
            raise ToolError(
                f"str_replace: 'old' not found in {path}. The text "
                "may have been edited since you last read it; "
                "re-read the file and try again with current "
                "context."
            )
        if match_count > 1:
            raise ToolError(
                f"str_replace: 'old' matches {match_count} times in "
                f"{path} — must be unique. Include more surrounding "
                "context (preceding/following lines) until the "
                "match is unique."
            )
        new_text = text.replace(old, new, 1)
        try:
            full.write_text(new_text, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"write failed for {path}: {exc}") from exc
        # Stash post-patch size for the observability hook —
        # comparison baseline for the bytes-saved-vs-full-write
        # analysis (T67).
        self._last_op_metadata = {
            "file_size_after_bytes": len(new_text.encode("utf-8"))
        }
        delta = len(new) - len(old)
        sign = "+" if delta >= 0 else ""
        return (
            f"str_replace applied to {path} "
            f"({sign}{delta} chars; was {len(text)}, now {len(new_text)})"
        )

    def insert(self, path: str, line_number: int, content: str) -> str:
        """Insert ``content`` after ``line_number`` in ``path``.
        Line numbers are 1-indexed. ``line_number=0`` prepends.

        ``content`` is inserted as a complete unit; if it lacks a
        trailing newline, one is added so the next line stays on
        its own line. The diff-cheap counterpart to ``str_replace``
        for adding new content (imports, methods, blocks) without
        having to re-send the whole file.

        Raises ToolError when ``line_number`` is out of bounds
        (< 0 or > len(lines)).
        """
        full = self._resolve(path)
        if not full.exists():
            raise ToolError(f"file not found: {path}")
        if not full.is_file():
            raise ToolError(f"not a file: {path}")
        try:
            text = full.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ToolError(
                f"file {path} is not valid UTF-8: {exc}"
            ) from exc
        # splitlines(keepends=True) preserves \n boundaries so we
        # can reassemble without losing line endings.
        lines = text.splitlines(keepends=True)
        if line_number < 0 or line_number > len(lines):
            raise ToolError(
                f"insert: line_number {line_number} out of bounds "
                f"for {path} (file has {len(lines)} lines; valid "
                f"range is 0..{len(lines)})"
            )
        # Ensure content ends with a newline so the insertion
        # doesn't fuse with the following line.
        if content and not content.endswith("\n"):
            content = content + "\n"
        # If the file's last line lacks a newline AND we're
        # inserting after it, add a newline to that line first so
        # the inserted content starts on its own line.
        if (
            line_number == len(lines)
            and lines
            and not lines[-1].endswith("\n")
        ):
            lines[-1] = lines[-1] + "\n"
        lines.insert(line_number, content)
        new_text = "".join(lines)
        try:
            full.write_text(new_text, encoding="utf-8")
        except OSError as exc:
            raise ToolError(f"write failed for {path}: {exc}") from exc
        # Stash post-patch size for the observability hook (T67).
        self._last_op_metadata = {
            "file_size_after_bytes": len(new_text.encode("utf-8"))
        }
        inserted_lines = content.count("\n")
        return (
            f"insert applied to {path} after line {line_number} "
            f"(+{inserted_lines} lines, +{len(content)} chars)"
        )

    def list_files(self, directory: str = ".", pattern: str | None = None) -> str:
        """List files under ``directory``, optionally matching a glob ``pattern``.

        Recursive when ``pattern`` is supplied (uses Pathlib's rglob);
        flat directory listing when ``pattern`` is None. Results are
        capped at ``MAX_LIST_ENTRIES`` with a trailing marker if more
        exist. Returns one path per line, sorted, relative to
        project_root for portability.
        """
        full = self._resolve(directory)
        if not full.exists():
            raise ToolError(f"directory not found: {directory}")
        if not full.is_dir():
            raise ToolError(f"not a directory: {directory}")
        try:
            if pattern is None:
                entries = sorted(full.iterdir())
            else:
                entries = sorted(full.rglob(pattern))
        except OSError as exc:
            raise ToolError(f"list failed for {directory}: {exc}") from exc

        # Filter to in-sandbox paths (rglob can follow weird symlinks).
        in_sandbox = [p for p in entries if p.resolve().is_relative_to(self._root)]

        # T-ab46: hide cross-milestone artifact filenames during
        # scoping/composition phases of a milestone-scoped workflow.
        # Filenames carry concept slugs; agents that see "story-XXX-
        # kohl-views-budget" in the listing reason "already have
        # stories for budget" and skip generating fresh material —
        # observed on obol-260522-1 M5 design where alice + cat
        # repeatedly emitted 0 stories despite T-ab35 blocking the
        # actual read_file calls. No-op outside the load-bearing
        # scoping/composition phases or when no scope is set.
        in_sandbox = self._filter_cross_milestone_paths(in_sandbox)

        truncated = len(in_sandbox) > MAX_LIST_ENTRIES
        if truncated:
            in_sandbox = in_sandbox[:MAX_LIST_ENTRIES]

        rendered = [str(p.relative_to(self._root)) for p in in_sandbox]
        if not rendered:
            return "(no entries)"
        result = "\n".join(rendered)
        if truncated:
            result += f"\n[truncated: {len(entries) - MAX_LIST_ENTRIES} more entries]"
        return result

    def grep(self, pattern: str, path: str = ".", ignore_case: bool = False) -> str:
        """Search for ``pattern`` (regex) in files under ``path``.

        Returns matched lines as ``relative/path:line_number:matched_text``,
        capped at ``MAX_GREP_HITS``. Skips files that aren't valid
        UTF-8. ``path`` may be a single file or a directory (recursive).
        """
        full = self._resolve(path)
        try:
            regex = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
        except re.error as exc:
            raise ToolError(f"invalid regex {pattern!r}: {exc}") from exc

        if not full.exists():
            raise ToolError(f"path not found: {path}")

        candidates: list[Path]
        if full.is_file():
            candidates = [full]
        elif full.is_dir():
            candidates = [p for p in full.rglob("*") if p.is_file()]
        else:
            raise ToolError(f"path is neither file nor directory: {path}")

        hits: list[str] = []
        for fpath in sorted(candidates):
            if not fpath.resolve().is_relative_to(self._root):
                continue
            try:
                with fpath.open(encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = fpath.relative_to(self._root)
                            hits.append(f"{rel}:{line_num}:{line.rstrip()}")
                            if len(hits) >= MAX_GREP_HITS:
                                break
            except UnicodeDecodeError:
                # Binary or non-UTF-8 file; skip silently. The LLM
                # gets the hits from text files, doesn't need to
                # know about binaries.
                continue
            except OSError:
                continue
            if len(hits) >= MAX_GREP_HITS:
                break

        if not hits:
            return f"(no matches for {pattern!r})"
        truncated = len(hits) >= MAX_GREP_HITS
        result = "\n".join(hits)
        if truncated:
            result += f"\n[truncated at {MAX_GREP_HITS} hits]"
        return result

    # ------------------------------------------------------------------ #
    # Git operations — the working tree IS the implementation artifact;
    # reviewers read git_diff to find what shipped.
    # ------------------------------------------------------------------ #

    def _run_git(self, args: list[str]) -> str:
        """Run ``git <args>`` in project_root. Returns stdout; raises
        ToolError if git isn't installed, the project isn't a repo, or
        the command failed. Output is capped at MAX_READ_BYTES so a
        diff against a large change doesn't flood the LLM context."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self._root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "git is not installed in this environment — "
                "git_status / git_diff are unavailable"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError(f"git {' '.join(args)} timed out after 10s") from exc
        if result.returncode != 0:
            stderr = result.stderr.strip() or "(no stderr)"
            if "not a git repository" in stderr.lower():
                raise ToolError(
                    f"project root {self._root} is not a git repository — "
                    "Runner.make_full_cast initializes one at setup; if you "
                    "see this, the project root was not set up via the Runner"
                )
            raise ToolError(f"git {' '.join(args)} failed: {stderr}")
        out = result.stdout
        if len(out.encode("utf-8")) > MAX_READ_BYTES:
            truncated = out[:MAX_READ_BYTES]
            return truncated + f"\n\n[truncated: output exceeded {MAX_READ_BYTES} bytes]"
        return out

    def git_status(self) -> str:
        """Show the working-tree state — files modified, added, deleted,
        or untracked since the last commit. Use this to find what work
        the meeting has produced before diving into specific files."""
        out = self._run_git(["status", "--porcelain=v1"])
        if not out.strip():
            return "(working tree clean — no changes since last commit)"
        return out

    # ------------------------------------------------------------------ #
    # Test execution — Tweedles in M5 use this to iterate red→green
    # against Hatter's failing tests. Without it, Tweedles ship code
    # blind and rely on M6 (Caterpillar's review) to surface failures
    # downstream — which often hits MEETING_BUDGET before the fix loop
    # closes. Running tests during M5 collapses the iteration distance.
    # ------------------------------------------------------------------ #

    def run_tests(
        self,
        paths: list[str] | None = None,
        timeout_seconds: float = DEFAULT_TEST_TIMEOUT_SECONDS,
    ) -> str:
        """Run pytest in the project root, return a compact result summary.

        Output is structured for LLM consumption — capped at
        MAX_TEST_OUTPUT_BYTES, summary line first, then short-form
        failures (one line each), then truncated tracebacks for the
        first few failures if budget allows.

        ``paths``: specific test files or test IDs (e.g.
        ``tests/test_foo.py`` or ``tests/test_foo.py::test_bar``). When
        None, runs the full suite (pytest's default discovery). Each
        path is sandbox-checked.

        ``timeout_seconds``: hard wall-clock cap; raises ToolError on
        expiration so the LLM can decide whether to narrow scope.

        Returns the compact summary string. Raises ToolError on setup
        failures (no Python interpreter, no pytest installed, sandbox
        escape, timeout). A failing pytest run is *not* an error — the
        return string conveys it via the summary.
        """
        cmd: list[str] = [sys.executable, "-m", "pytest", "--tb=short", "-q"]
        if paths:
            for p in paths:
                self._resolve(p)  # raises ToolError on sandbox escape
            cmd.extend(paths)

        try:
            result = subprocess.run(
                cmd,
                cwd=self._root,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "python interpreter not available — "
                "run_tests requires sys.executable to be valid"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError(
                f"pytest timed out after {timeout_seconds}s — "
                f"narrow the test scope with `paths` or fix a hung test"
            ) from exc

        return _format_pytest_output(result.stdout, result.stderr, result.returncode)

    def verify_imports(self, path: str, *, timeout_seconds: float = 15.0) -> str:
        """Static-check a single file for import + name-resolution bugs.

        The class of bug this catches lives BETWEEN code review and
        test execution: a Pydantic shadow field, a misnamed decorator,
        a missing import that yields ``NameError`` at runtime. M8
        review (reading code) reliably misses these; pytest catches
        them at collection — but only AFTER the team has already
        shipped. ``verify_imports`` lets Caterpillar run the check
        DURING review against a specific file, surfacing the bug
        before it lands.

        Implementation: invokes ruff with the pyflakes (F) + syntax
        (E9) rule families. Each diagnostic is one line in the output;
        on a clean file, returns ``OK: <path> passes static checks``.
        Non-Python files (``.ts``, ``.tsx``, ``.js``, ``.jsx``) get a
        pointer to npm_build instead — single-file frontend static
        checks aren't supported by this tool (tsc needs the full
        project context).

        ``path`` is sandboxed to the project root.
        ``timeout_seconds`` is a hard cap so a stuck ruff invocation
        doesn't block the review.
        """
        full = self._resolve(path)
        if not full.exists():
            raise ToolError(f"file not found: {path}")
        if not full.is_file():
            raise ToolError(f"not a file: {path}")
        suffix = full.suffix.lower()
        if suffix in (".ts", ".tsx", ".js", ".jsx"):
            return (
                f"verify_imports skipped for {path} — frontend "
                f"static checks need the full project context "
                f"(tsc / vite). Use the M9 ``npm_build`` check "
                f"for these files."
            )
        if suffix != ".py":
            raise ToolError(
                f"verify_imports only supports .py files (got "
                f"{suffix!r}). For frontend code rely on the M9 "
                f"npm_build verification."
            )
        ruff_bin = (
            shutil.which("ruff")
            or str(Path(sys.executable).parent / "ruff")
        )
        if not Path(ruff_bin).exists():
            raise ToolError(
                "ruff binary not found — verify_imports needs ruff "
                "on PATH or installed in the active Python "
                "environment. (Wonderland ships ruff as a dev "
                "dependency; this should always be available.)"
            )
        cmd = [
            ruff_bin, "check",
            "--select", "F,E9",
            "--no-fix",
            "--output-format", "concise",
            "--force-exclude",
            str(full),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise ToolError(
                f"verify_imports timed out after {timeout_seconds}s "
                f"on {path}"
            ) from exc
        if proc.returncode == 0:
            return f"OK: {path} passes static checks (pyflakes + syntax)."
        # Ruff exits non-zero when issues are found OR when it errors.
        # Either way, surface stdout (the diagnostics) + stderr (any
        # tool error) so the LLM gets the full picture.
        diagnostics = (proc.stdout or "").strip()
        errors = (proc.stderr or "").strip()
        # Trim to keep the bus payload sane.
        out = diagnostics if diagnostics else "(no diagnostics in stdout)"
        if errors and errors != diagnostics:
            out = f"{out}\n--- stderr ---\n{errors}"
        if len(out) > MAX_TEST_OUTPUT_BYTES:
            out = out[:MAX_TEST_OUTPUT_BYTES] + "\n[truncated]"
        return f"verify_imports findings for {path}:\n{out}"

    def exec_smoke_probe(
        self,
        snippet: str,
        *,
        timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS,
    ) -> str:
        """Run a Python snippet in the project root to exercise runtime
        behavior of changed code.

        The class of bug this catches lives BEYOND static review:
          - SQL CHECK constraints SQLite rejects at INSERT time
            (non-deterministic ``DATE('now')``, anything else
            SQLite refuses)
          - Schema drift that surfaces as FK violations or
            type-coercion bugs against existing DB state
          - Framework integration that 404s, deadlocks, or silently
            no-ops
          - File I/O that's denied at runtime but valid at parse time
          - Async coroutines that block on an awaited never-resolves

        Static review reading the diff reliably misses these; running
        the code surfaces them in seconds. Cat reaches for this when
        the diff touches side-effect-producing code (DB writes, SQL
        execution, file I/O, subprocess invocation, network calls).

        Implementation: invokes ``python -c <snippet>`` in the project
        root with stdin closed and a hard wall-clock timeout. Captures
        stdout + stderr + exit code. Truncates output to
        MAX_PROBE_OUTPUT_BYTES.

        Snippet length is capped at MAX_PROBE_SNIPPET_BYTES (16 KiB).
        A probe that needs more than that should land as a proper
        test under ``tests/`` instead — file it as a finding with a
        ``test_coverage_required: true`` request.

        Returns a formatted block:

            exit_code=N
            stdout:
            <captured stdout>
            stderr:
            <captured stderr>

        A non-zero exit_code is not a tool failure — it's the probe's
        primary signal. Most runtime bugs surface as an exception (
        non-zero exit + stderr traceback). The tool only raises
        ToolError on infrastructure problems (no Python interpreter,
        timeout, oversized snippet).
        """
        if not isinstance(snippet, str):
            raise ToolError(
                f"exec_smoke_probe expects a string snippet "
                f"(got {type(snippet).__name__})"
            )
        if not snippet.strip():
            raise ToolError(
                "exec_smoke_probe requires a non-empty snippet"
            )
        if len(snippet.encode("utf-8")) > MAX_PROBE_SNIPPET_BYTES:
            raise ToolError(
                f"snippet exceeds {MAX_PROBE_SNIPPET_BYTES} bytes — "
                f"narrow the probe to exercise just one code path, "
                f"or file it as a test under tests/ via a finding "
                f"with test_coverage_required=true"
            )
        cmd = [sys.executable, "-c", snippet]
        try:
            result = subprocess.run(
                cmd,
                cwd=self._root,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise ToolError(
                "python interpreter not available — exec_smoke_probe "
                "requires sys.executable to be valid"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ToolError(
                f"smoke probe timed out after {timeout_seconds}s — "
                f"narrow the probe to exercise less, or check whether "
                f"the code under test has an infinite loop / "
                f"blocking I/O"
            ) from exc

        stdout = (result.stdout or "").rstrip()
        stderr = (result.stderr or "").rstrip()
        parts = [f"exit_code={result.returncode}"]
        parts.append(
            f"stdout:\n{stdout}" if stdout else "stdout: (empty)"
        )
        parts.append(
            f"stderr:\n{stderr}" if stderr else "stderr: (empty)"
        )
        out = "\n".join(parts)
        if len(out.encode("utf-8")) > MAX_PROBE_OUTPUT_BYTES:
            out = out[:MAX_PROBE_OUTPUT_BYTES] + "\n[truncated]"
        return out

    def git_diff(self, path: str | None = None) -> str:
        """Show the diff of working-tree changes against HEAD.

        With no path, shows the full diff (all modified + added files).
        With a path, shows the diff for just that file (relative to
        project root). Includes untracked files via ``--no-index``
        diff against /dev/null when needed.

        Output is capped at MAX_READ_BYTES; use git_status first if
        the diff might be large, then narrow with a path."""
        # `git diff HEAD` shows tracked-file changes; for untracked
        # files we add them to the diff manually via diff --no-index.
        # The simplest path: stage everything to a virtual index, then
        # diff against HEAD. We use `git add -N` (intent-to-add) which
        # doesn't actually stage content but lets diff see new files.
        try:
            subprocess.run(
                ["git", "add", "-N", "."],
                cwd=self._root,
                capture_output=True,
                check=False,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # _run_git below will produce the proper error; don't
            # double-handle here.
            pass
        args = ["diff", "HEAD"]
        if path is not None:
            # Resolve path safely; reject escapes.
            self._resolve(path)  # raises ToolError on escape
            args.extend(["--", path])
        out = self._run_git(args)
        if not out.strip():
            return "(no diff — working tree matches HEAD)"
        return out

    # ------------------------------------------------------------------ #
    # Tool-use schema for Anthropic's API
    # ------------------------------------------------------------------ #

    @staticmethod
    def tool_definitions() -> list[dict[str, Any]]:
        """The Anthropic tool-use schema for these tools.

        Pass as ``tools=[...]`` to ``messages.create``. The LLM can
        request these by name; the Tweedle's deliberate() loop
        executes them and feeds the results back.
        """
        return [
            {
                "name": "read_file",
                "description": (
                    "Read the contents of a text file relative to the project "
                    "root. Returns UTF-8 text. Files larger than 64 KiB are "
                    "truncated (full-file reads only). Use this to inspect "
                    "existing code before editing it.\n\n"
                    "OPTIONAL line-range read via `offset` (1-indexed start "
                    "line) and `limit` (max lines to return). Prefer this "
                    "over full-file reads when you know which section you "
                    "need — when you've already grepped for a symbol and "
                    "want to read its definition, when you're checking a "
                    "specific function signature, when you've just written "
                    "to part of a file and want to verify a different "
                    "section. Line-range reads cut per-call token cost "
                    "5-10x for the common case of needing one block out "
                    "of a 200-line file. Output of a range read is "
                    "numbered (line N\\tcontent) so you can re-anchor on "
                    "the same range without re-reading.\n\n"
                    "MILESTONE ROSTER (scope-ownership lookups). The full "
                    "milestone roster lives at `.wonderland/milestones/` — "
                    "one `milestone-NN-<slug>.md` per milestone, each "
                    "carrying that milestone's Goal and Done-when. These "
                    "are readable cross-scope at ALL times (unlike "
                    "stories/features/tickets, which are scope-locked to "
                    "the active milestone during scoping/composition). "
                    "Before asking the operator 'which milestone owns "
                    "surface X?' (a route, a UI form, an endpoint, a card), "
                    "read_file the candidate milestone files and check "
                    "their Done-when — ownership is almost always already "
                    "declared there (e.g. a partner-entry form whose home "
                    "is named in a later milestone's Done-when). Resolve "
                    "ownership from the roster yourself instead of "
                    "escalating; this is boundary context, not the "
                    "milestone's work-items, so reading it won't pull "
                    "you off-scope."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                        "offset": {
                            "type": "integer",
                            "description": (
                                "Optional 1-indexed start line. Combine "
                                "with `limit` to read a window."
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                "Optional max number of lines to return. "
                                "Without offset, returns the first N lines."
                            ),
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "write_file",
                "description": (
                    "Write content to a text file (overwriting if it exists, "
                    "creating parent directories as needed). Use this for "
                    "*new* files or *wholesale rewrites*. For incremental "
                    "edits to an existing file (changing a line, adding a "
                    "method, fixing a return value), prefer `str_replace` "
                    "or `insert` — they're token-cheap because they send "
                    "only the diff instead of the whole file."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Full file content to write.",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            {
                "name": "delete_file",
                "description": (
                    "Delete a file from the project tree. Sandboxed "
                    "to project_root; refuses directories. Idempotent "
                    "on missing files (returns 'not found' rather "
                    "than failing). Use this for pruning duplicates — "
                    "e.g. dropping merged tickets during M3.5 "
                    "consolidation, or dropping orphaned files during "
                    "a review pass. Be conservative: deletion is "
                    "irreversible within a run."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "str_replace",
                "description": (
                    "Replace exactly one occurrence of `old` with `new` in "
                    "an existing file. The token-cheap diff primitive — "
                    "use this for incremental edits (fix a line, change a "
                    "return value, swap an import) instead of re-sending "
                    "the entire file via write_file. `old` must match "
                    "exactly once: zero matches means the file changed "
                    "since you last read it (re-read it); multiple matches "
                    "means you need more surrounding context to make the "
                    "match unique. Deletion is supported via `new=\"\"`."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                        "old": {
                            "type": "string",
                            "description": (
                                "Exact text to match (single occurrence "
                                "required). Include enough surrounding "
                                "context that the match is unambiguous."
                            ),
                        },
                        "new": {
                            "type": "string",
                            "description": (
                                "Replacement text. Use empty string to "
                                "delete the matched region."
                            ),
                        },
                    },
                    "required": ["path", "old", "new"],
                },
            },
            {
                "name": "insert",
                "description": (
                    "Insert content after a specific line in an existing "
                    "file. Line numbers are 1-indexed; use 0 to prepend at "
                    "the top of the file. Companion to `str_replace` for "
                    "additions where you don't have a unique anchor to "
                    "replace against (e.g., adding a new import block, "
                    "appending a method)."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path relative to the project root.",
                        },
                        "line_number": {
                            "type": "integer",
                            "description": (
                                "1-indexed line number after which to "
                                "insert. 0 = prepend (insert at top). "
                                "Must be in 0..len(lines)."
                            ),
                        },
                        "content": {
                            "type": "string",
                            "description": (
                                "Content to insert. A trailing newline "
                                "is added automatically if absent so the "
                                "insertion doesn't fuse with the next "
                                "line."
                            ),
                        },
                    },
                    "required": ["path", "line_number", "content"],
                },
            },
            {
                "name": "list_files",
                "description": (
                    "List files in a directory, optionally matching a glob "
                    "pattern (recursive when a pattern is supplied). Use this "
                    "to discover existing code before adding new files."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory path relative to the project root. Defaults to '.'.",
                        },
                        "pattern": {
                            "type": "string",
                            "description": "Optional glob pattern (e.g. '*.py'). When set, search is recursive.",
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "grep",
                "description": (
                    "Search for a regex pattern in files under a path "
                    "(recursive when path is a directory). Returns matched "
                    "lines as 'relative/path:line:text'. Use this to find "
                    "where something is defined or referenced before "
                    "deciding what to write."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Python regex pattern to search for.",
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory to search under. Defaults to '.'.",
                        },
                        "ignore_case": {
                            "type": "boolean",
                            "description": "Case-insensitive match. Defaults to false.",
                        },
                    },
                    "required": ["pattern"],
                },
            },
            {
                "name": "git_status",
                "description": (
                    "Show the working-tree state — files modified, added, "
                    "deleted, or untracked since the last commit. The "
                    "working tree IS the implementation artifact; this "
                    "tool tells you what work the meeting has produced. "
                    "Use it before reaching for git_diff so you know "
                    "which files to focus on."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
            {
                "name": "run_tests",
                "description": (
                    "Run pytest in the project root. Returns a compact "
                    "summary: total pass/fail/skip counts, the short-form "
                    "list of failing tests, and truncated tracebacks for "
                    "the first few failures. Use this during M5 (the "
                    "implementation phase) to iterate red→green: ship "
                    "code with write_file, run the relevant tests, read "
                    "what's still failing, fix and repeat. Without this, "
                    "you ship blind and rely on M6 review to find what's "
                    "broken — much slower and more expensive. Specify "
                    "`paths` to scope to particular test files or test "
                    "IDs (e.g. 'tests/test_feature_001.py' or "
                    "'tests/test_feature_001.py::test_happy_path'); "
                    "omit to run the full suite. A failing pytest is "
                    "NOT an error — the result string conveys the state."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "paths": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional list of test files or test IDs. "
                                "Omit to run the full suite (slowest but "
                                "most thorough). Narrow when iterating "
                                "on a specific failure."
                            ),
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "description": (
                                "Hard wall-clock cap for the pytest run. "
                                "Defaults to 60s. Increase for slow "
                                "suites; decrease when narrowing scope."
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "git_diff",
                "description": (
                    "Show the diff of working-tree changes against HEAD. "
                    "With no path, shows the full diff (all modified and "
                    "added files in unified format). With a path, shows "
                    "the diff for just that file. Reviewers read this to "
                    "find what shipped without consulting separate "
                    "metadata. If the diff would be large, call "
                    "git_status first and narrow with a path."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Optional path (relative to project root) "
                                "to scope the diff to a single file or "
                                "directory."
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "verify_imports",
                "description": (
                    "Run a static import + name-resolution check on a "
                    "single Python file (pyflakes + syntax via ruff). "
                    "Catches the class of bug that lives BETWEEN code "
                    "review and test execution: a Pydantic shadow "
                    "field, a misnamed decorator (``@app.get`` instead "
                    "of ``@router.get``), a missing import that yields "
                    "``NameError`` at runtime, a forward reference "
                    "that doesn't resolve. M8 reviews reading code "
                    "reliably miss these; pytest catches them at "
                    "collection — but only after the team has "
                    "shipped. Run this DURING review to surface the "
                    "bug before the next implementation pass. Returns "
                    "either ``OK: <path> passes static checks`` or a "
                    "list of diagnostics with file:line context. "
                    "Frontend files (.ts/.tsx/.js/.jsx) are skipped — "
                    "use the M9 ``npm_build`` check for those."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": (
                                "Path (relative to project root) of the "
                                ".py file to check."
                            ),
                        },
                    },
                    "required": ["path"],
                },
            },
            {
                "name": "exec_smoke_probe",
                "description": (
                    "Execute a Python snippet in the project root to "
                    "probe the runtime behavior of changed code. "
                    "Catches the class of bug that lives BEYOND "
                    "static review: SQL CHECK constraints SQLite "
                    "rejects at INSERT time (non-deterministic "
                    "``DATE('now')``), schema drift that surfaces as "
                    "FK violations or type-coercion bugs against "
                    "existing DB state, framework integration that "
                    "404s or no-ops silently, async coroutines that "
                    "deadlock, file I/O that's denied at runtime but "
                    "valid at parse time. Reach for this DURING "
                    "review when the diff touches anything that "
                    "produces side effects — DB writes, SQL "
                    "execution, file I/O, subprocess invocation, "
                    "network calls. Static review alone reliably "
                    "misses runtime failures in these paths. Keep "
                    "the snippet small: a few imports + a single "
                    "function call exercising the happy path with "
                    "realistic inputs is usually enough. A non-zero "
                    "exit code is not a tool failure — it's the "
                    "probe's primary signal. Returns "
                    "``exit_code=N\\nstdout:<...>\\nstderr:<...>``, "
                    "truncated to ~4 KiB."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "snippet": {
                            "type": "string",
                            "description": (
                                "Python source to execute. Runs in the "
                                "project root, so package imports work "
                                "normally. Keep concise — under 16 KiB; "
                                "under 30 lines for typical probes."
                            ),
                        },
                        "timeout_seconds": {
                            "type": "number",
                            "description": (
                                "Optional wall-clock cap in seconds "
                                "(default 30.0). Tighten for probes "
                                "that should complete instantly; "
                                "loosen if exercising a deliberately "
                                "slow path."
                            ),
                        },
                    },
                    "required": ["snippet"],
                },
            },
        ]

    def execute(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        *,
        agent_id: str | None = None,
    ) -> str:
        """Dispatch a tool call by name. Raises ToolError on failure.

        The Tweedle's tool-use loop calls this for each tool_use block
        in the LLM's response, then packages the return value (or
        ToolError message) into a tool_result block for the next turn.

        ``agent_id`` is the calling agent's name for tool-call
        observability (T66). Optional; the writer captures the
        invocation regardless, with agent_id=None when callers don't
        propagate it (synthetic test calls, primarily).
        """
        # Capture the call's timing + sizes + error for the
        # observability hook. Done at the dispatcher rather than
        # per-method so adding a new tool primitive doesn't require
        # remembering to instrument it.
        start = time.monotonic()
        timestamp = datetime.now(tz=timezone.utc)
        result_str: str | None = None
        error_msg: str | None = None
        # Clear the per-call metadata stash so a previous call's
        # file_size_after doesn't leak forward.
        self._last_op_metadata = None
        try:
            if tool_name == "read_file":
                result_str = self.read_file(
                    tool_input["path"],
                    offset=tool_input.get("offset"),
                    limit=tool_input.get("limit"),
                )
            elif tool_name == "write_file":
                result_str = self.write_file(
                    tool_input["path"], tool_input["content"]
                )
            elif tool_name == "delete_file":
                result_str = self.delete_file(tool_input["path"])
            elif tool_name == "str_replace":
                result_str = self.str_replace(
                    tool_input["path"],
                    tool_input["old"],
                    tool_input["new"],
                )
            elif tool_name == "insert":
                result_str = self.insert(
                    tool_input["path"],
                    int(tool_input["line_number"]),
                    tool_input["content"],
                )
            elif tool_name == "list_files":
                result_str = self.list_files(
                    tool_input.get("directory", "."),
                    tool_input.get("pattern"),
                )
            elif tool_name == "grep":
                result_str = self.grep(
                    tool_input["pattern"],
                    tool_input.get("path", "."),
                    tool_input.get("ignore_case", False),
                )
            elif tool_name == "git_status":
                result_str = self.git_status()
            elif tool_name == "git_diff":
                result_str = self.git_diff(tool_input.get("path"))
            elif tool_name == "run_tests":
                result_str = self.run_tests(
                    paths=tool_input.get("paths"),
                    timeout_seconds=tool_input.get(
                        "timeout_seconds", DEFAULT_TEST_TIMEOUT_SECONDS
                    ),
                )
            elif tool_name == "verify_imports":
                result_str = self.verify_imports(tool_input["path"])
            elif tool_name == "exec_smoke_probe":
                result_str = self.exec_smoke_probe(
                    tool_input["snippet"],
                    timeout_seconds=tool_input.get(
                        "timeout_seconds", DEFAULT_PROBE_TIMEOUT_SECONDS
                    ),
                )
            else:
                raise ToolError(f"unknown tool: {tool_name}")
            return result_str
        except ToolError as exc:
            error_msg = str(exc)
            raise
        except Exception as exc:  # noqa: BLE001
            # Other exceptions still get observed before propagating.
            error_msg = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if self._on_tool_call is not None:
                args_summary, input_bytes = _summarize_tool_args(
                    tool_name, tool_input
                )
                metadata = self._last_op_metadata or {}
                event = ToolCallEvent(
                    timestamp=timestamp,
                    tool_name=tool_name,
                    agent_id=agent_id,
                    args_summary=args_summary,
                    input_bytes=input_bytes,
                    elapsed_ms=(time.monotonic() - start) * 1000.0,
                    result_bytes=(
                        len(result_str.encode("utf-8"))
                        if result_str is not None
                        else 0
                    ),
                    error=error_msg,
                    file_size_after_bytes=metadata.get(
                        "file_size_after_bytes"
                    ),
                )
                # Writer is sync + best-effort; never let an
                # observability failure mask the underlying tool
                # result.
                try:
                    self._on_tool_call(event)
                except Exception:  # noqa: BLE001
                    pass


def _format_pytest_output(stdout: str, stderr: str, returncode: int) -> str:
    """Compress pytest output into an LLM-friendly summary.

    Pytest dumps tens of KB of output for a moderately-failing suite —
    too much for a Tweedle's tool_result context. We extract the
    structured bits the LLM needs to iterate red→green:

    1. The terminal summary line (e.g. "16 passed, 48 failed in 9.14s")
    2. The short test summary section (one line per failure)
    3. Truncated failure tracebacks for the first ~3 failures, if
       budget allows.

    Pytest exit codes:
      0 — all tests passed
      1 — at least one test failed
      2 — pytest was interrupted
      3 — internal error
      4 — usage error (bad CLI args)
      5 — no tests collected
    """
    # Detect collection failures (broken import chain) FIRST, before
    # any exit-code-specific handling. When pytest can't load a test
    # module (or its conftest.py) because some import fails, it can't
    # collect ANY tests — every other test in the project is invisible
    # until the import is fixed. This surface is *higher priority*
    # than test failures because it hides all other test signal.
    #
    # Pytest's exit code for collection failures varies: a conftest
    # ImportError exits 4 ("usage error"); a test-module ImportError
    # may exit 2 with collection error in stdout; a missing module
    # might exit 1. So we can't rely on returncode alone — we scan
    # both stdout and stderr for telltale patterns and let that
    # supersede the exit-code branches below.
    combined = stdout + "\n" + stderr
    collection_error_match = re.search(
        r"ERROR\s+collecting\s+([^\n]+)", combined
    )
    import_error_match = re.search(
        r"^(?:E\s+)?(ImportError|ModuleNotFoundError):\s+([^\n]+)",
        combined,
        re.MULTILINE,
    )
    if collection_error_match or import_error_match:
        msg_parts = [
            "BUILD FAILURE — pytest could not collect tests because the "
            "import chain is broken. NO test signal is available until "
            "this is fixed."
        ]
        if collection_error_match:
            msg_parts.append(
                f"Collection error in: {collection_error_match.group(1).strip()}"
            )
        if import_error_match:
            msg_parts.append(
                f"{import_error_match.group(1)}: {import_error_match.group(2).strip()}"
            )
        # Try to find the file:line where the import fails.
        traceback_match = re.search(
            r"^([\w\-/]+\.py):(\d+):\s*in\s+",
            combined,
            re.MULTILINE,
        )
        if traceback_match:
            msg_parts.append(
                f"Failure traceback ends at: "
                f"{traceback_match.group(1)}:{traceback_match.group(2)}"
            )
        msg_parts.append(
            "Common cause: a file you replaced or deleted is still being "
            "imported elsewhere. Check api/__init__.py and other "
            "aggregator files for stale imports of removed symbols."
        )
        return "\n\n".join(msg_parts)

    # Exit-code-specific handling for non-collection-error cases.
    if returncode == 5:
        # No tests collected — usually a path issue or empty test dir.
        clean_stderr = stderr.strip()[:200] or "(no stderr)"
        return f"pytest collected no tests. stderr: {clean_stderr}"
    if returncode == 4:
        clean_stderr = stderr.strip()[:200] or "(no stderr)"
        return f"pytest usage error (bad arguments). stderr: {clean_stderr}"
    if returncode == 3:
        clean_stderr = stderr.strip()[:200] or "(no stderr)"
        return (
            f"pytest internal error. stderr: {clean_stderr}\n"
            f"stdout (last 200 chars): ...{stdout[-200:]}"
        )

    # Final summary line. Pytest's format depends on verbosity:
    #   default verbosity: "========= 2 passed in 0.05s ========="
    #   quiet (-q):        "2 passed in 0.05s"
    # Match both — optional leading/trailing `=` decorations, but the
    # body always starts with a count + outcome and ends with "in Xs".
    summary_match = re.search(
        r"^(?:=+\s*)?(\d+\s+(?:passed|failed|skipped|error|errors)[^=\n]*?in\s+[\d.]+\s*s)(?:\s*=+)?\s*$",
        stdout,
        re.MULTILINE,
    )
    summary = summary_match.group(1).strip() if summary_match else "(could not parse summary)"

    # Short test summary section — one line per failed test.
    short_summary = ""
    short_match = re.search(
        r"=+\s*short test summary info\s*=+\n(.+?)(?:\n=+|\Z)",
        stdout,
        re.DOTALL,
    )
    if short_match:
        short_summary = short_match.group(1).strip()

    parts = [f"pytest result: {summary}"]
    if short_summary:
        lines = [ln for ln in short_summary.splitlines() if ln.strip()]
        max_lines = 12
        shown = lines[:max_lines]
        parts.append("\nFailing tests:")
        parts.append("\n".join(shown))
        if len(lines) > max_lines:
            parts.append(f"\n... and {len(lines) - max_lines} more")

    result = "\n".join(parts)

    # If we have headroom under the cap, append truncated failure
    # tracebacks for the first few failures from the FAILURES section.
    failures_match = re.search(
        r"=+\s*FAILURES\s*=+\n(.+?)\n=+\s*(?:warnings summary|short test summary info|=)",
        stdout,
        re.DOTALL,
    )
    if failures_match and len(result) < MAX_TEST_OUTPUT_BYTES // 2:
        failures_block = failures_match.group(1)
        # Each failure starts with "_____ test_name _____"
        failure_chunks = re.split(r"\n_+\s.+?\s_+\n", failures_block)
        # First chunk is empty (split before first separator); take next 3
        failure_chunks = [c.strip() for c in failure_chunks if c.strip()][:3]
        if failure_chunks:
            available = MAX_TEST_OUTPUT_BYTES - len(result) - 200
            traceback_section = "\n\nFirst failures (tracebacks):\n"
            traceback_section += "\n---\n".join(failure_chunks)
            if len(traceback_section) > available:
                traceback_section = traceback_section[:available] + "\n[truncated]"
            result += traceback_section

    if len(result.encode("utf-8")) > MAX_TEST_OUTPUT_BYTES:
        result = result[:MAX_TEST_OUTPUT_BYTES] + "\n\n[output truncated]"
    return result


__all__ = [
    "DEFAULT_TEST_TIMEOUT_SECONDS",
    "MAX_GREP_HITS",
    "MAX_LIST_ENTRIES",
    "MAX_READ_BYTES",
    "MAX_TEST_OUTPUT_BYTES",
    "ToolError",
    "Tools",
]
