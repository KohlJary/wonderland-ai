"""Cross-run seed continuity via disk-backed artifact fallback.

Per analysis 039 / r41-obol redux: when a workflow runs against a
project that already has artifacts on disk from prior runs, the
existing seed-resolution logic only sees utterances on the in-memory
bus. If an upstream agent stays silent because their work "already
exists" (e.g. Alice doesn't re-emit stories that are still in
``.wonderland/stories/``), downstream meetings get empty seeds and
fall over.

This module bridges the gap: when ``resolve_seeds`` finds nothing on
the bus for a given binding's kind filter, it falls back to reading
disk-backed artifacts from the corresponding registry and synthesizes
seed utterances that look just like the ones an agent would have
emitted live. Downstream meetings see them indistinguishably.

The synthesis is intentionally minimal:
  - Speaker = the agent who normally produces this kind (Alice for
    stories, Rabbit for tickets/features, Cat for ADRs, etc.)
  - speech_act = the kind's expected speech_act
  - Body = the file's full text on disk
  - Artifact = single Artifact with ``payload = {title, slug, number,
    path}`` — sufficient for slug-based per-iteration slicing in
    ``resolve_seeds``
  - is_seed = True
  - timestamp = file mtime (gives downstream code a meaningful order)

Bus content always wins over disk content: when the bus has matching
utterances, the disk fallback never fires for that binding. This
preserves the "current run's emissions are authoritative" invariant.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from wonderland.utterance import (
    AgentIdentity,
    Artifact,
    SpeechAct,
    Utterance,
    UtteranceContent,
)


def _load_tickets(project_root: Path) -> list[Any]:
    from wonderland.ticket import TicketRegistry

    return TicketRegistry(project_root).list_tickets()


def _load_stories(project_root: Path) -> list[Any]:
    from wonderland.story import StoryRegistry

    return StoryRegistry(project_root).list_stories()


def _load_features(project_root: Path) -> list[Any]:
    from wonderland.feature import FeatureRegistry

    return FeatureRegistry(project_root).list_features()


def _load_adrs(project_root: Path) -> list[Any]:
    from wonderland.adr import ADRRegistry

    return ADRRegistry(project_root).list_adrs()


def _load_contract_notes(project_root: Path) -> list[Any]:
    from wonderland.contract_note import ContractNoteRegistry

    return ContractNoteRegistry(project_root).list_contract_notes()


def _load_test_scenarios(project_root: Path) -> list[Any]:
    from wonderland.test_scenario import TestScenarioRegistry

    return TestScenarioRegistry(project_root).list_scenarios()


def _load_implementations(project_root: Path) -> list[Any]:
    from wonderland.implementation import ImplementationRegistry

    return ImplementationRegistry(project_root).list_implementations()


def _load_reviews(project_root: Path) -> list[Any]:
    from wonderland.review import ReviewRegistry

    return ReviewRegistry(project_root).list_reviews()


def _load_observations(project_root: Path) -> list[Any]:
    from wonderland.observation import ObservationRegistry

    return ObservationRegistry(project_root).list_observations()


# kind → (loader, default_speaker_name, speech_act)
#
# default_speaker_name: the agent whose constitution makes this their
# primary output. Synthetic utterances claim authorship from this
# agent; downstream seed consumers can't tell the difference between
# a freshly-emitted artifact and a disk-restored one.
#
# speech_act: the SpeechAct enum value an agent uses when emitting
# this kind. Most kinds map 1:1 (story → STORY, ticket → TICKET).
# ADRs are unusual — Cat emits them as PROPOSAL with an `adr`-kind
# artifact, not a hypothetical SpeechAct.ADR (no such enum value).
_LOADERS: dict[str, tuple[Callable[[Path], list[Any]], str, SpeechAct]] = {
    "ticket": (_load_tickets, "white_rabbit", SpeechAct.TICKET),
    "story": (_load_stories, "alice", SpeechAct.STORY),
    "feature": (_load_features, "white_rabbit", SpeechAct.FEATURE),
    "adr": (_load_adrs, "cheshire_cat", SpeechAct.PROPOSAL),
    "contract_note": (
        _load_contract_notes,
        "tweedledee",
        SpeechAct.CONTRACT_NOTE,
    ),
    "test_scenario": (
        _load_test_scenarios,
        "mad_hatter",
        SpeechAct.TEST_SCENARIO,
    ),
    "implementation": (
        _load_implementations,
        "tweedledum",
        SpeechAct.IMPLEMENTATION,
    ),
    "review": (_load_reviews, "caterpillar", SpeechAct.REVIEW),
    "observation": (_load_observations, "dormouse", SpeechAct.OBSERVATION),
}


def supported_disk_kinds() -> frozenset[str]:
    """Kinds for which disk fallback is wired. Useful for callers
    that want to know which bindings can fall back vs. which can't."""
    return frozenset(_LOADERS.keys())


def disk_seeds_for_kinds(
    project_root: Path,
    kinds: list[str],
    *,
    thread_id: str,
) -> list[Utterance]:
    """Synthesize seed utterances by reading on-disk artifacts.

    For each kind in ``kinds`` whose loader is registered, scan the
    project's ``.wonderland/<dirname>/`` directory and produce one
    synthetic Utterance per file. Returns an empty list when:
      - project_root has no .wonderland/ directory yet
      - no kinds match registered loaders
      - all matching kinds have empty registries

    The thread_id is set to the source-meeting id by callers; this
    is what the seed binding's ``from`` field names. Per-iteration
    slicing in resolve_seeds then handles routing the right slug to
    the right iteration.
    """
    out: list[Utterance] = []
    for kind in kinds:
        loader_entry = _LOADERS.get(kind)
        if loader_entry is None:
            continue
        loader, speaker_name, speech_act = loader_entry
        try:
            records = loader(project_root)
        except Exception:  # noqa: BLE001 — best-effort; missing dirs etc.
            continue
        for record in records:
            try:
                body = record.path.read_text(encoding="utf-8")
            except OSError:
                body = ""
            try:
                mtime = datetime.fromtimestamp(
                    record.path.stat().st_mtime, tz=UTC
                )
            except OSError:
                mtime = datetime.now(UTC)
            artifact = Artifact(
                kind=kind,
                payload={
                    "title": getattr(record, "title", ""),
                    "slug": getattr(record, "slug", ""),
                    "number": getattr(record, "number", 0),
                    "path": str(record.path),
                },
            )
            out.append(
                Utterance(
                    thread_id=thread_id,
                    speaker=AgentIdentity(
                        name=speaker_name,
                        # "0.1" matches the default constitution_version
                        # the runtime uses for live agents in the same
                        # cast. Synthetic utterances inherit this so
                        # downstream identity comparisons don't see
                        # an outlier version string.
                        constitution_version="0.1",
                    ),
                    addressed_to="caucus",
                    speech_act=speech_act,
                    content=UtteranceContent(body=body, artifacts=[artifact]),
                    is_seed=True,
                    timestamp=mtime,
                )
            )
    return out


__all__ = [
    "disk_seeds_for_kinds",
    "supported_disk_kinds",
]
