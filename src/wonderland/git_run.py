"""Per-run git plumbing — branch creation at run start, commit at
run end, optional fast-forward merge back to the originating branch.

The substrate already initializes the project as a git repo on first
run (``runner._ensure_git_repo``) so Caterpillar's git_diff has a
baseline. This module layers per-run branch isolation on top:

- ``open_run_branch(project_root, run_id)`` checks out a fresh
  ``wonderland/<run_id>`` branch off the current HEAD, returning the
  source-branch name so callers can record it.
- ``commit_run(project_root, run_id, message)`` stages everything in
  the working tree and creates a commit on the run branch. Silent
  no-op when nothing changed (a design-only run that produced no code
  diff still uses this; the commit just doesn't fire).
- ``attempt_merge(project_root, source_branch)`` switches back to the
  source branch and fast-forwards the run branch in. Returns
  ``MergeOutcome`` so the caller can surface ``MERGED`` / ``CONFLICT``
  / ``SOURCE_MOVED`` to the operator.

Every function tolerates a missing git binary or an uninitialized
repo by returning ``None`` / a no-op outcome — the operator's run
still completes, and the git steps just don't fire.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


RUN_BRANCH_PREFIX = "wonderland"
DEFAULT_TIMEOUT_SECONDS = 15


class MergeOutcome(StrEnum):
    """Why the merge attempt landed where it did. Surfaced to the
    operator via a notification on the live-run / dashboard surface."""

    MERGED = "merged"          # fast-forward succeeded
    CONFLICT = "conflict"      # merge needed manual resolution
    SOURCE_MOVED = "source_moved"  # source branch moved during run
    SKIPPED = "skipped"        # no source branch recorded or no-op
    GIT_UNAVAILABLE = "git_unavailable"


@dataclass(frozen=True)
class MergeResult:
    outcome: MergeOutcome
    detail: str = ""


def _run_git(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Thin wrapper that runs git with consistent timeout + capture
    settings. Raises ``CalledProcessError`` on non-zero exit when
    ``check`` is true; callers decide what to do per-command."""
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=timeout,
    )


def _current_branch(project_root: Path) -> str | None:
    """Return the current branch name. ``None`` if detached HEAD or
    git unavailable."""
    try:
        result = _run_git(
            ["rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    branch = result.stdout.strip()
    if not branch or branch == "HEAD":
        return None
    return branch


def open_run_branch(project_root: Path, run_id: str) -> str | None:
    """Checkout ``wonderland/<run_id>`` from the current HEAD. Returns
    the source-branch name (the branch HEAD was on when this fired)
    so callers can later attempt a merge back. Returns ``None`` if
    git is unavailable, the repo isn't initialized, or HEAD is
    detached — the run still proceeds; it just won't be isolated.
    """
    if not (project_root / ".git").exists():
        return None
    source = _current_branch(project_root)
    if source is None:
        return None
    target = f"{RUN_BRANCH_PREFIX}/{run_id}"
    try:
        _run_git(
            ["checkout", "-b", target],
            cwd=project_root,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return source


def commit_run(
    project_root: Path, run_id: str, message: str
) -> bool:
    """Stage every working-tree change + commit. No-op when the
    working tree is clean. Returns True if a commit landed, False
    otherwise (including silent failure paths)."""
    if not (project_root / ".git").exists():
        return False
    try:
        _run_git(["add", "-A"], cwd=project_root)
        # Check if there's anything to commit.
        status = _run_git(
            ["status", "--porcelain"],
            cwd=project_root,
        )
        if not status.stdout.strip():
            return False
        full_message = (
            f"wonderland run {run_id}\n\n{message}"
            if message.strip()
            else f"wonderland run {run_id}"
        )
        _run_git(
            ["commit", "-m", full_message],
            cwd=project_root,
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def attempt_merge(
    project_root: Path, source_branch: str | None
) -> MergeResult:
    """Switch back to ``source_branch`` and fast-forward the current
    run branch in. ``source_branch=None`` skips the merge (no source
    was recorded). FF-only merge — if the source moved during the
    run, we leave the branch in place for the operator to resolve
    manually rather than risking a confused 3-way merge."""
    if not source_branch:
        return MergeResult(MergeOutcome.SKIPPED, "no source branch recorded")
    if not (project_root / ".git").exists():
        return MergeResult(
            MergeOutcome.GIT_UNAVAILABLE, "no git repo"
        )
    run_branch = _current_branch(project_root)
    if run_branch is None or not run_branch.startswith(
        f"{RUN_BRANCH_PREFIX}/"
    ):
        return MergeResult(
            MergeOutcome.SKIPPED,
            "current branch isn't a run branch — leaving alone",
        )
    try:
        _run_git(["checkout", source_branch], cwd=project_root)
    except subprocess.CalledProcessError as exc:
        return MergeResult(
            MergeOutcome.CONFLICT,
            f"couldn't switch to {source_branch}: "
            f"{(exc.stderr or '').strip()[:200]}",
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return MergeResult(MergeOutcome.GIT_UNAVAILABLE, "git failed")
    # FF merge. ``--ff-only`` errors if source moved.
    try:
        _run_git(
            ["merge", "--ff-only", run_branch],
            cwd=project_root,
        )
    except subprocess.CalledProcessError as exc:
        # Re-check whether source advanced past the fork point —
        # the most common reason ff-only fails. Either way we
        # leave the operator on the source branch with the run
        # branch still intact for manual resolution.
        return MergeResult(
            MergeOutcome.SOURCE_MOVED,
            f"fast-forward failed: "
            f"{(exc.stderr or '').strip()[:200]}",
        )
    return MergeResult(
        MergeOutcome.MERGED, f"merged {run_branch} into {source_branch}"
    )


__all__ = [
    "MergeOutcome",
    "MergeResult",
    "RUN_BRANCH_PREFIX",
    "attempt_merge",
    "commit_run",
    "open_run_branch",
]
