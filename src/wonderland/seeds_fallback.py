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


def _record_has_live_work(record: Any, project_root: Path, citing_kind: str) -> bool:
    """True when a record represents operator-queued / in-flight work — a
    feature/ticket in QUEUED or IN_PROGRESS lifecycle state. Such a record
    must survive the phantom-citation filter even when its upstream
    citations are stale, so queued work never silently drops out of the
    implement lane. Best-effort: any lookup failure → not-live (filter
    proceeds as before)."""
    slug = getattr(record, "slug", None)
    if not slug:
        return False
    try:
        if citing_kind == "feature":
            # Roll up the feature's TICKETS directly (not get_state, which
            # short-circuits to None when the feature has no transition-log
            # history) — a feature is live iff it has queued/in-flight work.
            from wonderland.feature_lifecycle import (
                FeatureState,
                _derive_post_ticket_state,
            )

            return _derive_post_ticket_state(project_root, slug) in (
                FeatureState.QUEUED, FeatureState.IN_PROGRESS,
            )
        if citing_kind == "ticket":
            from wonderland.ticket_lifecycle import TicketState, get_state

            return get_state(project_root, slug) in (
                TicketState.QUEUED, TicketState.IN_PROGRESS,
            )
    except Exception:  # noqa: BLE001 — best-effort
        return False
    return False


def _filter_phantom_citations(
    records: list[Any],
    project_root: Path,
    *,
    citing_kind: str,
    sources_parser: Callable[[str], list[str]],
) -> list[Any]:
    """Drop records whose on-disk ``sources`` contain NO citation
    that resolves to a real artifact on disk.

    Surfaced by obol M3 (substrate bug ``0c98c694``): a feature
    whose stories were retracted or whose .md files disappeared
    after the feature was emitted carries phantom citations through
    every downstream meeting that pulls it as a seed. The
    on-emission strip (``_apply_source_resolution_for_utterance``)
    catches phantoms at the moment the artifact is composed, but
    can't catch drift that happens later. This read-time filter is
    the after-the-fact backstop.

    Citing kinds:
      - ``"feature"`` — sources should resolve to stories.
      - ``"ticket"`` — sources may resolve to features OR stories.

    **At-least-one-anchor semantics.** A record is dropped ONLY
    when *every* source citation fails to resolve — meaning the
    artifact is fully unmoored. When at least one source resolves
    (typically the parent feature for a ticket, or one of the
    parent stories for a feature), the record is well-anchored
    and additional unresolved citations are tolerated as
    process-artifact noise.

    The earlier "all sources must resolve" rule was too strict for
    tickets: substrate-synthesized follow-up tickets legitimately
    cite review slugs (e.g. ``build-check-verify-failed``,
    ``database-schema-initialization-and-seeded-data-loading``),
    cross-ticket-coherence review titles, and occasionally
    prefixed forms (``feature-001-...``) that look like phantoms
    to a strict feature/story-only resolver but are real process
    references. Dropping tickets on those alone left the pipeline
    iterating only the small subset whose sources happened to be
    plain feature slugs — observed on obol-demo2 M1 where the
    pipeline kept selecting the same 3 done tickets while 5+
    legitimate queued tickets were filtered out (substrate bug
    ``088c204b``).

    Records whose source-line can't be parsed are kept (the parser
    is a single-line markdown extractor; an unreadable feature is
    a different bug class — not a phantom-citation case). Records
    whose ``path`` can't be read at all are dropped silently.

    Operator visibility: each fully-unanchored filtered record is
    logged at WARNING so it surfaces in any pilot log capture.
    Partial-phantoms (record kept despite some unresolved sources)
    log at DEBUG so they're observable in detailed traces without
    polluting normal output.
    """
    import logging

    # Lazy-import to keep this module load-light.
    from wonderland.workflow import collect_phantom_citations

    clean: list[Any] = []
    for record in records:
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable file — different bug class; skip silently.
            continue
        sources = sources_parser(text)
        if not sources:
            # No citations to validate (empty or unparseable line) —
            # keep the record; downstream handles empty-sources case.
            clean.append(record)
            continue
        phantoms = collect_phantom_citations(
            sources, project_root, citing_kind=citing_kind,
        )
        if phantoms and len(phantoms) == len(sources):
            # Exemption: never strand operator-queued work. A feature or
            # ticket the operator has QUEUED (or that's IN_PROGRESS) is LIVE
            # regardless of whether its upstream story/feature citations
            # still resolve — the citations can go stale across design
            # re-runs while the downstream work the operator queued stays
            # valid. Dropping it here is how queued tickets silently vanish
            # from the implement lane ("no tickets to work" with no reason).
            if _record_has_live_work(record, project_root, citing_kind):
                logging.warning(
                    "seeds_fallback KEEPING %s %r despite all-phantom "
                    "sources %s — it has queued/in-progress work, so it's "
                    "live. The **Sources:** line is stale (fix it when "
                    "convenient), but the work is NOT dropped.",
                    citing_kind, record.slug, phantoms,
                )
                clean.append(record)
                continue
            # FULLY unanchored AND no live work — drop with WARNING so
            # the operator sees the cleanup.
            logging.warning(
                "seeds_fallback dropping %s %r — ALL %d sources are "
                "phantom citations: %s. The artifact is fully "
                "unmoored from any real feature/story on disk; "
                "filtered from the seed pool to prevent downstream "
                "meeting loops. Clean up the citations manually "
                "(edit the **Sources:** line) or retract the "
                "orphan record.",
                citing_kind, record.slug, len(sources), phantoms,
            )
            continue
        if phantoms:
            # PARTIAL phantoms — record is anchored via at least
            # one resolving source; the rest are process-noise
            # citations (review slugs, build-check refs, etc.) and
            # tolerated. Log at DEBUG for traceability without
            # polluting normal output.
            logging.debug(
                "seeds_fallback keeping %s %r despite %d/%d phantom "
                "sources: %s (anchored via at least one resolving "
                "citation)",
                citing_kind, record.slug, len(phantoms), len(sources),
                phantoms,
            )
        clean.append(record)
    return clean


def _load_tickets(project_root: Path) -> list[Any]:
    from wonderland.ticket import TicketRegistry
    from wonderland.coverage import _parse_feature_sources

    all_tickets = TicketRegistry(project_root).list_tickets()
    # Ticket sources cite features OR stories. Same phantom-citation
    # parser as features (single ``**Sources:**`` comma-separated line).
    return _filter_phantom_citations(
        all_tickets, project_root,
        citing_kind="ticket",
        sources_parser=_parse_feature_sources,
    )


def _load_stories(project_root: Path) -> list[Any]:
    """Load stories from disk. When an active milestone scope is set,
    filter to stories whose ``realizes_requirements`` intersects the
    active milestone's ``consumes_requirements`` — stories from
    sibling milestones don't pollute the current milestone's design
    pass.

    Observed on obol-demo2 M2 design pass: without this filter,
    Alice's M2 scoping meeting saw every story Alice wrote during
    M1 design (milestone scope set, branching memory excluded
    M1 deliberation from recall, but the disk-loader seed pool
    still surfaced them). The result: M2 composition built on top
    of M1 story material, defeating the milestone scoping the
    operator just spent design budget setting up.

    Stories with empty ``realizes_requirements`` are dropped from
    scope (they pre-date the field or were poorly attributed at
    write time). Operators can backfill the field if the story
    is legitimately cross-milestone.
    """
    from wonderland.story import StoryRegistry

    all_stories = StoryRegistry(project_root).list_stories()

    # Lazy-import to avoid circular dep at module load.
    try:
        from wonderland.workflow import get_active_milestone_scope
        scope = get_active_milestone_scope()
    except Exception:  # noqa: BLE001
        scope = None
    if scope is None:
        return all_stories

    # Resolve the active milestone's consumes_requirements.
    try:
        from wonderland.coverage import (
            _parse_milestone_consumes,
            _parse_story_realizes,
            _parse_story_milestone,
        )
    except Exception:  # noqa: BLE001
        return all_stories  # parser unavailable, fall through

    milestone_dir = project_root / ".wonderland" / "milestones"
    if not milestone_dir.is_dir():
        return all_stories
    active_reqs: set[str] = set()
    for path in milestone_dir.glob("milestone-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Match by slug appearing in the filename; defensive because
        # milestone GUIDs vary and slug is the stable identifier.
        if scope.slug not in path.name:
            continue
        active_reqs.update(_parse_milestone_consumes(text))

    if not active_reqs:
        # Couldn't resolve the active milestone's requirements
        # (file missing, parser failed). Defensive: return all
        # stories rather than wedge the meeting on empty seeds.
        return all_stories

    in_scope: list[Any] = []
    for record in all_stories:
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            continue
        # T-ab7: explicit milestone field is authoritative when
        # present. Strip guid prefix (slug-only form is what the
        # scope holds). When set to a different milestone, drop
        # the story from this scope; when set to the active scope,
        # include it directly without consulting realizes. Stories
        # without the field fall through to the legacy intersection
        # filter on realizes_requirements (back-compat for stories
        # shipped before T-ab7). The legacy path leaks across
        # milestones via shared cross-cutting requirements (scope /
        # constraint / persona slugs consumed by many milestones) —
        # the explicit field exists precisely to bypass that leak.
        explicit = _parse_story_milestone(text)
        if explicit:
            slug_only = explicit.split(":", 1)[1] if ":" in explicit else explicit
            if slug_only == scope.slug:
                in_scope.append(record)
            continue
        story_reqs = set(_parse_story_realizes(text))
        # Drop stories that explicitly attribute to other milestones'
        # requirements only. Stories without realizes_requirements
        # are pre-attribution / legacy — also drop, operator backfills.
        if story_reqs & active_reqs:
            in_scope.append(record)
    return in_scope


def _load_features(project_root: Path) -> list[Any]:
    """Load features from disk. Two filters applied, in order:

    1. **Phantom-citation filter** (substrate bug ``0c98c694``): drop
       features whose on-disk ``Sources:`` line cites stories that no
       longer resolve. Catches drift that happens AFTER the on-emission
       strip — e.g. a story gets retracted but features citing it
       weren't cascade-updated, OR a story's .md file went missing
       (bug ``d9c120d4``). Without this filter, broken-citation features
       leaked into every downstream milestone's seed pool, causing the
       obol M3 caucus loop on Feature 002.

    2. **Milestone-scope filter** (mvp-demo2 M3 wedge fix): when an
       active milestone scope is set, drop features whose primary
       milestone (strongest Jaccard overlap of sources against
       milestone story-scope, ties on milestone order) isn't the
       active scope. Rabbit composing for M3 doesn't need M1/M2's
       features in his context.
    """
    from wonderland.feature import FeatureRegistry
    from wonderland.coverage import _parse_feature_sources

    all_features = FeatureRegistry(project_root).list_features()

    # Step 1: drop features with phantom citations. The defensive
    # default that USED to silently include unattributable features
    # (``if primary is None: include``) was masking exactly this
    # class of drift; phantoms now get logged + dropped explicitly.
    citation_clean = _filter_phantom_citations(
        all_features, project_root,
        citing_kind="feature",
        sources_parser=_parse_feature_sources,
    )

    # Step 2: milestone-scope filter. Lazy-import to avoid circular
    # dep at module load.
    try:
        from wonderland.workflow import get_active_milestone_scope
        scope = get_active_milestone_scope()
    except Exception:  # noqa: BLE001
        scope = None
    if scope is None:
        return citation_clean

    # Filter via the primary-milestone-per-feature heuristic:
    # strongest-overlap-wins (Jaccard similarity of feature.sources
    # against milestone story-scope), ties on milestone order.
    # Features whose primary is NOT the active scope get dropped
    # from this seed pool. Unattributable features (no overlap with
    # any milestone) stay in — defensive, but now sharply narrowed
    # because the step-1 filter already dropped the most common
    # cause of unattributability (phantom citations producing zero
    # Jaccard overlap with every milestone).
    primary_map = _compute_primary_milestone_per_feature(project_root)
    if not primary_map:
        return citation_clean  # no attribution possible, don't filter

    in_scope: list[Any] = []
    for record in citation_clean:
        primary = primary_map.get(record.slug)
        if primary is None or primary == scope.slug:
            in_scope.append(record)
    return in_scope


def _compute_primary_milestone_per_feature(
    project_root: Path,
) -> dict[str, str]:
    """Mirror of the dashboard's primary-milestone attribution
    (strongest source-set overlap, ties on milestone order).
    Returns feature_slug → primary_milestone_slug. Empty dict when
    project has no milestones or no features.

    TODO: extract this + the dashboard's copy into a shared module
    when there's time. For now duplicated to keep the seed-fallback
    fix surgical.
    """
    import re
    try:
        from wonderland.coverage import (
            _parse_milestone_consumes,
            _parse_story_realizes,
            _parse_feature_sources,
            _parse_feature_milestone,
        )
    except Exception:  # noqa: BLE001
        return {}

    milestone_dir = project_root / ".wonderland" / "milestones"
    if not milestone_dir.is_dir():
        return {}

    milestone_meta: list[tuple[str, int, list[str]]] = []
    for path in milestone_dir.glob("milestone-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        slug_m = re.search(r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE)
        order_m = re.search(r"^\*\*Order:\*\*\s*(\d+)", text, re.MULTILINE)
        if not slug_m or not order_m:
            continue
        milestone_meta.append((
            slug_m.group(1).strip(),
            int(order_m.group(1)),
            _parse_milestone_consumes(text),
        ))
    milestone_meta.sort(key=lambda x: (x[1], x[0]))
    if not milestone_meta:
        return {}

    story_re = re.compile(
        r"story-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
    )
    req_to_stories: dict[str, set[str]] = {}
    story_root = project_root / ".wonderland" / "stories"
    if story_root.is_dir():
        for p in story_root.glob("story-*.md"):
            m = story_re.match(p.name)
            if not m:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except OSError:
                continue
            for r in _parse_story_realizes(text):
                req_to_stories.setdefault(r, set()).add(m.group(1))

    milestone_scope: dict[str, set[str]] = {}
    for ms, _, consumes in milestone_meta:
        scope_set: set[str] = set()
        for r in consumes:
            scope_set |= req_to_stories.get(r, set())
        milestone_scope[ms] = scope_set

    feat_re = re.compile(
        r"feature-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
    )
    primary: dict[str, str] = {}
    feature_root = project_root / ".wonderland" / "features"
    if not feature_root.is_dir():
        return primary
    known_milestone_slugs = {ms for ms, _, _ in milestone_meta}
    for p in feature_root.glob("feature-*.md"):
        m = feat_re.match(p.name)
        if not m:
            continue
        fslug = m.group(1)
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        # T-ab5: explicit milestone field is authoritative when
        # present and resolvable. Strip guid prefix (slug-only form
        # is what the milestone meta tuple holds). Jaccard fallback
        # below only applies when the field is absent / unresolvable
        # — i.e., legacy features shipped before T-ab5.
        explicit = _parse_feature_milestone(text)
        if explicit:
            slug_only = explicit.split(":", 1)[1] if ":" in explicit else explicit
            if slug_only in known_milestone_slugs:
                primary[fslug] = slug_only
                continue
        raw_sources = _parse_feature_sources(text)
        # T-g5: strip guid prefix
        sources: set[str] = set()
        for s in raw_sources:
            sources.add(s.split(":", 1)[1] if ":" in s else s)
        if not sources:
            continue
        best: tuple[int, int, str] | None = None
        best_ms = ""
        for ms, morder, _ in milestone_meta:
            overlap = len(sources & milestone_scope[ms])
            if overlap == 0:
                continue
            key = (-overlap, morder, ms)
            if best is None or key < best:
                best = key
                best_ms = ms
        if best is not None:
            primary[fslug] = best_ms
    return primary


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
    context so agents can amend rather than restart.

    T-ab9 milestone-scope filter: when an active milestone scope is
    set (tdd-design/tdd-implement with ``--milestone <slug>``), only
    surface the active milestone's artifact. Sibling milestones are
    summarized in the framing block as "already shipped" / "future
    milestone" rather than seeded as full artifacts — full artifacts
    contain done-when + consumes detail that downstream agents treat
    as actionable scope. Mvp-demo-rerun-A M2 leak: Rabbit composed
    a foundation feature in M2's composition because M1's full
    milestone artifact (slug "m1-foundation-data-layer-api-contract",
    body describing SQLite schema + FastAPI stubs) was visible in
    seeds despite the framing block calling M1 "already shipped".

    No-active-scope flows (milestone-plan re-runs, ad-hoc workflows)
    still see all milestones — that's the expected behavior when
    the workflow is project-level rather than milestone-scoped.
    """
    from wonderland.milestone import MilestoneRegistry

    records = MilestoneRegistry(project_root).list_milestones()
    try:
        from wonderland.workflow import get_active_milestone_scope
        scope = get_active_milestone_scope()
    except Exception:  # noqa: BLE001
        scope = None
    if scope is not None:
        records = [r for r in records if r.slug == scope.slug]
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


def _load_diagrams(project_root: Path) -> list[Any]:
    """P21 — surface the current diagram stack into design meetings so
    agents update/extend it rather than re-draw from scratch. The seed
    body is each ``.oph`` file (via ``.path``), so the agent sees the
    actual structure + component names (keeping names stable preserves
    node GUIDs + their ticket links).

    Milestone-scoped: when a milestone is active, only diagrams with at
    least one node whose component name appears in the milestone's
    goal/done-when text are seeded. The whole-app stack (milestone-plan
    draws every surface up front) otherwise invites a single milestone's
    design pass to decompose surfaces it doesn't own — M2 was shown the
    full three-card dashboard and overshot into weather/news work. Dropping
    the auth/partner diagrams from a weather milestone's seed keeps the pass
    focused. Over-inclusive on purpose (a shared diagram with ANY in-scope
    node is kept) — starving design of needed context is worse than a bit
    of extra."""
    from wonderland.diagrams.registry import DiagramRegistry

    registry = DiagramRegistry(project_root)

    milestone_tokens: frozenset[str] | None = None
    try:
        from wonderland.workflow import get_active_milestone_scope

        scope = get_active_milestone_scope()
    except Exception:  # noqa: BLE001
        scope = None
    if scope is not None and getattr(scope, "slug", None):
        from wonderland.diagrams.linking import _title_tokens
        from wonderland.milestone import MilestoneRegistry

        for rec in MilestoneRegistry(project_root).list_milestones():
            if rec.slug == scope.slug:
                try:
                    milestone_tokens = _title_tokens(
                        rec.path.read_text(encoding="utf-8")
                    )
                except OSError:
                    milestone_tokens = None
                break

    out: list[Any] = []
    for slug in registry.list_slugs():
        diagram = registry.read(slug)
        if diagram is None:
            continue
        if milestone_tokens is not None and not _diagram_in_milestone_scope(
            diagram, milestone_tokens
        ):
            continue
        out.append(_RegistryRecordAdapter(diagram))
    return out


def _diagram_in_milestone_scope(diagram: Any, milestone_tokens: frozenset) -> bool:
    """True if any of the diagram's component nodes is named in the
    milestone text (its distinctive tokens all appear). Reuses the
    node↔ticket matcher's tokenizer so scope-relevance and link-relevance
    agree."""
    from wonderland.diagrams.linking import _distinctive_tokens

    for node in diagram.nodes:
        distinctive = _distinctive_tokens(node.name)
        if distinctive and distinctive <= milestone_tokens:
            return True
    return False


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
    # P21 diagrams — the structural build-tracker. milestone-plan lays
    # the initial stack; tdd-design meetings read it via from: any
    # kinds: [diagram] so composition can refine/extend it as features
    # take shape. Speaker = Rabbit (canonical structure owner).
    "diagram": (_load_diagrams, "white_rabbit", SpeechAct.DIAGRAM),
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
