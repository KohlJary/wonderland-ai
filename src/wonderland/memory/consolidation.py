"""Milestone-close consolidation for episodic memory branches.

T-a2 chunk C. When the last unverified feature in a milestone
transitions to VERIFIED, the substrate fires
``consolidate_milestone`` to:

  1. Generate a structured project-level summary utterance describing
     what shipped (which features, which contracts, which decisions).
  2. Write the summary to every per-agent EpisodicStore at the
     project branch (so future runs' inheritance_chain reads see it).
  3. Archive the milestone's design and impl branches in every per-
     agent store (rewrite ``design:<slug>`` → ``archived:design:<slug>``,
     ``impl:<slug>`` → ``archived:impl:<slug>``). Still on disk for
     forensics; excluded from default agent reads.

The summary is substrate-generated (deterministic, free, no LLM
call). If we want fancier LLM-authored summaries later, Mock Turtle
is the natural fit — but the deterministic version is the right
default per "ship the cheap version first."

The summary's speaker is Mock Turtle (the memory keeper persona) —
even though no LLM call happens, the persona attribution maintains
the constitutional fiction that the memory keeper is the one
producing the long-arc summaries.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from wonderland.artifact_guid import new_artifact_guid
from wonderland.memory.episodic import (
    ARCHIVED_PREFIX,
    PROJECT_BRANCH,
    EpisodicStore,
)
from wonderland.utterance import (
    AgentIdentity,
    SpeechAct,
    Utterance,
    UtteranceContent,
)

if TYPE_CHECKING:
    pass


_MEMORY_DIRNAME = "memory"
_CONSOLIDATION_SPEAKER = "mock_turtle"
_CONSOLIDATION_VERSION = "0.1"
_CONSOLIDATION_THREAD = "milestone-consolidation"


def _list_agent_dirs(project_root: Path) -> list[Path]:
    """Find every per-agent memory directory in the project."""
    memory_root = project_root / ".wonderland" / _MEMORY_DIRNAME
    if not memory_root.is_dir():
        return []
    return [
        d for d in memory_root.iterdir()
        if d.is_dir() and (d / "episodic.sqlite").is_file()
    ]


def _build_summary_body(
    milestone_slug: str,
    milestone_name: str | None,
    feature_slugs: list[str],
) -> str:
    """Compose the project-level summary body. Structured so future
    branches reading the project chain see a stable shape.

    Intentionally terse — captures the conclusions (what shipped),
    not the deliberation (the design pass's argument churn).
    """
    name_part = (
        f" ({milestone_name})" if milestone_name else ""
    )
    features_block = "\n".join(
        f"  - {slug}" for slug in feature_slugs
    ) if feature_slugs else "  (none)"
    return (
        f"Milestone closed: ``{milestone_slug}``{name_part}.\n\n"
        f"Shipped features:\n{features_block}\n\n"
        f"Design + implementation branches for this milestone have "
        f"been archived. Subsequent design passes inherit this "
        f"summary via the project-branch read chain; per-milestone "
        f"deliberation does NOT cross-bleed."
    )


def _build_summary_utterance(
    milestone_slug: str,
    milestone_name: str | None,
    feature_slugs: list[str],
) -> Utterance:
    """Build the summary utterance to write at project level."""
    body = _build_summary_body(milestone_slug, milestone_name, feature_slugs)
    return Utterance(
        id=new_artifact_guid(),
        thread_id=_CONSOLIDATION_THREAD,
        parent_id=None,
        speaker=AgentIdentity(
            name=_CONSOLIDATION_SPEAKER,
            constitution_version=_CONSOLIDATION_VERSION,
        ),
        addressed_to="caucus",
        speech_act=SpeechAct.OBSERVATION,
        content=UtteranceContent(body=body, artifacts=[]),
        timestamp=datetime.now(timezone.utc),
    )


async def consolidate_milestone(
    project_root: Path,
    *,
    milestone_slug: str,
    milestone_name: str | None = None,
    feature_slugs: list[str] | None = None,
    branch_prefixes: tuple[str, ...] = ("design:", "impl:"),
) -> dict[str, int]:
    """Fire milestone-close consolidation across every per-agent
    EpisodicStore in the project.

    For each agent:
      - Record a project-level summary utterance (attributed to
        Mock Turtle).
      - Archive any branches starting with ``design:<slug>`` or
        ``impl:<slug>`` (configurable via ``branch_prefixes``).

    Returns a dict mapping agent_name -> total archived utterance
    count, for observability + telemetry.

    Idempotent: re-running on the same milestone is a no-op for
    already-archived branches and a duplicate summary record (which
    INSERT OR IGNORE silently drops on id collision — but each
    consolidation gets a fresh GUID, so duplicates accumulate; if
    that's a problem, dedupe by checking project branch for an
    existing summary referencing this milestone slug).
    """
    if feature_slugs is None:
        feature_slugs = []
    summary = _build_summary_utterance(
        milestone_slug, milestone_name, feature_slugs
    )
    branches_to_archive = tuple(
        f"{prefix}{milestone_slug}" for prefix in branch_prefixes
    )
    results: dict[str, int] = {}

    for agent_dir in _list_agent_dirs(project_root):
        agent_name = agent_dir.name
        archived_count = 0
        async with EpisodicStore(project_root, agent_name) as store:
            await store.record_at_branch(summary, PROJECT_BRANCH)
            for branch in branches_to_archive:
                archived_count += await store.archive_branch(branch)
        results[agent_name] = archived_count

    return results


__all__ = [
    "consolidate_milestone",
]
