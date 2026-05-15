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


def _load_requirements(project_root: Path) -> list[Any]:
    """P14 requirement artifacts. Speaker varies by which interviewer
    produced the requirement (Alice/Cat/Rabbit) but for synthetic-
    seed purposes we attribute to alice (the first interviewer in
    the discovery workflow); downstream meetings just need the
    artifact's body, not authorship.

    Adapter records carry the same shape (.path / .title / .slug /
    .number / .body) as the other loaders' records, so the
    synthesis path doesn't need to special-case milestones."""
    from wonderland.interview import RequirementRegistry

    records = RequirementRegistry(project_root).list_requirements()
    return [_RegistryRecordAdapter(r) for r in records]


def _load_milestones(project_root: Path) -> list[Any]:
    """P15 milestone artifacts. Speaker = white_rabbit (the canonical
    plan owner). milestone-plan re-runs read these as cross-run
    context so agents can amend rather than restart."""
    from wonderland.milestone import MilestoneRegistry

    records = MilestoneRegistry(project_root).list_milestones()
    return [_RegistryRecordAdapter(r) for r in records]


class _RegistryRecordAdapter:
    """Adapter shaping a RequirementRecord or MilestoneRecord like
    the other loader records (StoryRecord, TicketRecord, etc.).
    The bodies of those registries already render to the standard
    markdown shape; this just exposes .body for the synthesis path
    that reads file contents."""

    def __init__(self, record: Any) -> None:
        self.path = record.path
        self.title = getattr(record, "title", None) or getattr(
            record, "name", record.slug
        )
        self.slug = record.slug
        self.number = getattr(record, "number", None) or getattr(
            record, "order", 0
        )
        # Body read lazily by the synthesis path; just exposing the
        # path is enough for the existing pipeline.


def _load_observations(project_root: Path) -> list[Any]:
    from wonderland.observation import ObservationRegistry

    return ObservationRegistry(project_root).list_observations()


class _DirectiveRecord:
    """Adapter so the directive loader can return objects with the
    same shape as Story/Ticket/Feature records: ``.path``, ``.title``,
    ``.slug``, ``.number``. The body extractor below pulls
    ``preset.body`` instead of reading the YAML envelope so seed
    consumers see just the operator's prompt, not the metadata
    around it.
    """

    def __init__(self, path: Path, preset: Any) -> None:
        self.path = path
        self.title = preset.title or preset.name
        self.slug = preset.name
        self.number = 0
        self.body = preset.body


class _ProjectContextRecord:
    """Adapter exposing the standard ``.path`` / ``.title`` /
    ``.slug`` / ``.number`` shape so the ``project_context`` loader
    plugs into the same disk-fallback pipeline as story / ticket /
    feature loaders. ``.body`` carries the rendered prose summary
    (not the YAML envelope) so agents read facts, not metadata.
    """

    def __init__(self, path: Path, context: Any, body: str) -> None:
        self.path = path
        self.title = context.name
        self.slug = context.name
        self.number = 0
        self.body = body


def _load_project_context(project_root: Path) -> list[Any]:
    """Read ``<project>/.wonderland/project.yaml`` if present and
    return a single synthetic record carrying the rendered context
    body. Empty list when no project context has been written —
    legacy projects without context memory operate from directive
    grounding only.
    """
    from wonderland.project_context import (
        load_project_context,
        project_context_path,
        render_context_body,
    )

    context = load_project_context(project_root)
    if context is None:
        return []
    body = render_context_body(context)
    return [
        _ProjectContextRecord(
            path=project_context_path(project_root),
            context=context,
            body=body,
        )
    ]


def _load_directives(project_root: Path) -> list[Any]:
    """Read ``<project>/.wonderland/directives/*.yaml`` as
    ``_DirectiveRecord`` instances. Operator's launching prompt
    (the ``body`` field of each preset) becomes a seed kind that
    architecturally-load-bearing meetings (e.g. Cat's M4) can
    request via ``from: any kinds: [directive]`` — keeps stack
    constraints in the literal directive visible during ADR work
    instead of relying on stories paraphrasing them.
    """
    from wonderland.directive import (
        list_project_directives,
        load_project_directive,
        project_directives_dir,
    )

    out: list[Any] = []
    base = project_directives_dir(project_root)
    if not base.is_dir():
        return out
    for name in list_project_directives(project_root):
        try:
            preset = load_project_directive(name, project_root)
        except Exception:  # noqa: BLE001 — best-effort
            continue
        out.append(_DirectiveRecord(base / f"{name}.yaml", preset))
    return out


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
    # P14 requirements — synthesized by Alice (first interviewer in
    # the discovery workflow). Downstream meetings (milestone-plan,
    # tdd-design) read these via from: any kinds: [requirement].
    "requirement": (
        _load_requirements,
        "alice",
        SpeechAct.INTERVIEW_REVIEW,
    ),
    # P15 milestones — synthesized by Rabbit (canonical plan owner).
    # tdd-design --milestone reads these via from: any kinds:
    # [milestone] then filters on slug.
    "milestone": (
        _load_milestones,
        "white_rabbit",
        SpeechAct.MILESTONE_PLAN,
    ),
    # The Dodo "speaks" the directive in-run via relay_directive.
    # When restoring from disk for a meeting that didn't see the
    # original launch (e.g. M4 architecture), we attribute the
    # synthetic utterance to the Dodo too — keeps the speaker
    # identity consistent with the in-run path.
    "directive": (_load_directives, "dodo", SpeechAct.DIRECTIVE),
    # Project context memory — authoritative project-level facts
    # (stack, entry point, conventions). Surfaced into M4 / M5 /
    # M8 seed contexts so architectural + contract decisions can
    # ground in the project's actual runtime shape, not the
    # Tweedles' default web-app prior. Speaker = Dodo (relay-
    # the-operator) since the Dodo is the team's interface to
    # what the operator wants and project context is operator-
    # authored.
    "project_context": (_load_project_context, "dodo", SpeechAct.DIRECTIVE),
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
            # Some record types carry a pre-extracted body (directives
            # wrap a YAML envelope around the operator's literal prompt;
            # we want just the prompt). Default path is the on-disk
            # file's full text — what stories/tickets/etc. need.
            preset_body = getattr(record, "body", None)
            if preset_body is not None:
                body = preset_body
            else:
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
