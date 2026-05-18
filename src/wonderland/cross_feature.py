"""Cross-feature ticket consolidation (M3.75) — T-a5.

When parallel M3 decomposition runs across multiple features in
the same tdd-design pass, the agents sometimes produce
near-duplicate tickets — the same upstream story slug ends up
sourced by tickets attributed to different features. Validation5
and mvp-demo both surfaced this pattern: "sqlite schema for notes"
showed up as separate tickets under both the persistence feature
and the test-infra feature.

M3.5 (per-feature consolidation) catches duplicates WITHIN a feature.
M3.75 catches duplicates ACROSS features.

This is substrate-side detection + auto-retract. No agent calls.
Deterministic; cheap.

Algorithm:
  1. Read all tickets on disk + their parent-feature attribution.
  2. Strip parent-feature slugs from each ticket's sources to get
     its "upstream interest set" (stories + reqs + ADRs the ticket
     was decomposed against).
  3. Cluster tickets by upstream interest set: any two tickets with
     identical sets are candidates for consolidation if they live
     under different parent features.
  4. For each cluster, score each candidate parent feature by how
     well its sources overlap the ticket's upstream interest. The
     feature with the strongest match wins; its ticket is kept;
     the others get transitioned to ABORTED + their files left on
     disk for forensics.

Conservative thresholds: only consolidates on EXACT match of
non-parent sources. Looser fuzzy matching is a follow-up if this
proves too conservative — false negatives (missing some dupes)
are better than false positives (collapsing legitimately-distinct
tickets).
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from wonderland.feature import FeatureRegistry
from wonderland.ticket import TicketRegistry
from wonderland.ticket_lifecycle import (
    IllegalTransitionError,
    TicketState,
    back_fill_state,
    get_state as get_ticket_state,
    transition as ticket_transition,
)


_SOURCES_RE = re.compile(r"^\*\*Sources?:\*\*\s*(.+?)$", re.MULTILINE)


def _parse_ticket_sources(ticket_md: str) -> list[str]:
    """Extract source slugs from a ticket markdown's **Sources:** line.
    Strips T-g5 guid:slug prefixes, returns plain slugs."""
    m = _SOURCES_RE.search(ticket_md)
    if m is None:
        return []
    raw = m.group(1).strip()
    sources: list[str] = []
    for part in raw.split(","):
        s = part.strip()
        if not s:
            continue
        # T-g5: guid:slug → slug
        if ":" in s:
            s = s.split(":", 1)[1]
        sources.append(s)
    return sources


def _parse_feature_sources(feature_md: str) -> list[str]:
    """Same as ticket sources — features use the same Sources line shape."""
    return _parse_ticket_sources(feature_md)


@dataclass(frozen=True)
class ConsolidationDecision:
    """One per cross-feature duplicate cluster — names the kept
    ticket + the retracted ones + the cluster's identifying
    upstream-source set."""

    kept_slug: str
    kept_parent_feature: str
    retracted_slugs: tuple[str, ...]
    upstream_sources: frozenset[str]

    def summary(self) -> str:
        return (
            f"Kept ``{self.kept_slug}`` (parent: ``{self.kept_parent_feature}``); "
            f"retracted {len(self.retracted_slugs)}: "
            f"{', '.join(self.retracted_slugs)}. "
            f"Cluster sources: {sorted(self.upstream_sources)}"
        )


def _build_feature_index(
    project_root: Path,
) -> tuple[set[str], dict[str, frozenset[str]]]:
    """Return (set_of_feature_slugs, feature_slug → frozenset(feature_sources))."""
    feature_root = project_root / ".wonderland" / "features"
    if not feature_root.is_dir():
        return set(), {}

    feature_slugs: set[str] = set()
    feature_sources: dict[str, frozenset[str]] = {}
    feature_filename_re = re.compile(
        r"feature-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
    )
    for path in feature_root.glob("feature-*.md"):
        m = feature_filename_re.match(path.name)
        if not m:
            continue
        slug = m.group(1)
        feature_slugs.add(slug)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        feature_sources[slug] = frozenset(_parse_feature_sources(text))
    return feature_slugs, feature_sources


def _ticket_parent_feature(
    sources: list[str], feature_slugs: set[str],
) -> str | None:
    """Identify which feature slug appears in the ticket's sources —
    that's the parent feature per the M3 attribution mechanism.

    Returns None when no feature slug is found (orphan ticket;
    skip from consolidation since it's not attributable to a
    cluster).
    """
    for s in sources:
        if s in feature_slugs:
            return s
    return None


def _score_parent_match(
    upstream: frozenset[str], feature_sources: frozenset[str],
) -> float:
    """Jaccard similarity between a ticket's upstream interest and a
    candidate parent feature's source set. Higher = stronger match."""
    if not upstream or not feature_sources:
        return 0.0
    intersection = upstream & feature_sources
    union = upstream | feature_sources
    return len(intersection) / len(union) if union else 0.0


def find_cross_feature_duplicates(
    project_root: Path,
) -> list[ConsolidationDecision]:
    """Compute consolidation decisions without applying them.

    Returns a list of ConsolidationDecision — one per duplicate
    cluster spanning ≥2 distinct parent features. Empty list when
    no cross-feature duplicates exist.

    Pure read-side analysis; no on-disk mutations.
    """
    registry = TicketRegistry(project_root)
    tickets = registry.list_tickets()
    if not tickets:
        return []

    feature_slugs, feature_sources = _build_feature_index(project_root)
    if not feature_slugs:
        return []

    # ticket_slug → (parent_feature, upstream_sources_frozenset)
    ticket_info: dict[str, tuple[str, frozenset[str]]] = {}
    for record in tickets:
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            continue
        sources = _parse_ticket_sources(text)
        parent = _ticket_parent_feature(sources, feature_slugs)
        if parent is None:
            continue
        # Upstream = all source slugs except the parent feature itself
        upstream = frozenset(s for s in sources if s != parent)
        if not upstream:
            # Ticket sources ONLY name the parent feature — no
            # cluster signal. Skip.
            continue
        ticket_info[record.slug] = (parent, upstream)

    # Cluster: upstream_set → list[(ticket_slug, parent_feature)]
    clusters: dict[frozenset[str], list[tuple[str, str]]] = defaultdict(list)
    for ticket_slug, (parent, upstream) in ticket_info.items():
        clusters[upstream].append((ticket_slug, parent))

    decisions: list[ConsolidationDecision] = []
    for upstream, members in clusters.items():
        # Need ≥2 members AND ≥2 distinct parent features to count
        # as a cross-feature duplicate cluster.
        parents = {p for _, p in members}
        if len(members) < 2 or len(parents) < 2:
            continue

        # Score each member by how well its parent feature's sources
        # align with the upstream set. Higher score wins.
        scored: list[tuple[float, str, str]] = []
        for ticket_slug, parent in members:
            score = _score_parent_match(
                upstream, feature_sources.get(parent, frozenset())
            )
            scored.append((score, ticket_slug, parent))

        # Tie-break: highest score, then alphabetical slug for
        # determinism.
        scored.sort(key=lambda x: (-x[0], x[1]))
        winner_score, winner_slug, winner_parent = scored[0]
        retracted = tuple(
            slug for _score, slug, _parent in scored[1:]
        )
        decisions.append(ConsolidationDecision(
            kept_slug=winner_slug,
            kept_parent_feature=winner_parent,
            retracted_slugs=retracted,
            upstream_sources=upstream,
        ))

    return decisions


def consolidate_cross_feature_duplicates(
    project_root: Path,
    *,
    actor: str = "wonderland-substrate",
) -> list[ConsolidationDecision]:
    """Find + apply cross-feature ticket consolidation.

    For each ConsolidationDecision, transitions every retracted
    ticket to ABORTED via ticket_lifecycle. The file is LEFT on
    disk (forensics + audit trail); only the lifecycle marks it
    aborted. Operator can prune later via the dashboard if desired.

    Returns the list of decisions actually applied (excludes
    decisions where the lifecycle transition failed — best-effort,
    consolidate-what-we-can semantics).
    """
    decisions = find_cross_feature_duplicates(project_root)
    applied: list[ConsolidationDecision] = []
    for decision in decisions:
        any_applied = False
        for ticket_slug in decision.retracted_slugs:
            try:
                current = get_ticket_state(project_root, ticket_slug)
                if current == TicketState.ABORTED:
                    # Already aborted — nothing to do.
                    any_applied = True
                    continue
                # ABORTED is only reachable from IN_PROGRESS per the
                # lifecycle. Back-fill straight to IN_PROGRESS (no
                # actual implementation work happened; this is a
                # consolidation move not a worked-then-aborted move,
                # but the transition graph requires it).
                if current is None:
                    back_fill_state(
                        project_root, ticket_slug,
                        TicketState.IN_PROGRESS,
                        notes=(
                            "Back-fill to in_progress for "
                            "cross-feature consolidation abort"
                        ),
                    )
                    current = TicketState.IN_PROGRESS
                # Walk PENDING → QUEUED → IN_PROGRESS → ABORTED as
                # needed.
                consolidation_notes = (
                    f"Cross-feature consolidation: "
                    f"duplicate of {decision.kept_slug!r} "
                    f"under feature {decision.kept_parent_feature!r}"
                )
                walk = []
                if current == TicketState.PENDING:
                    walk = [
                        TicketState.QUEUED,
                        TicketState.IN_PROGRESS,
                        TicketState.ABORTED,
                    ]
                elif current == TicketState.QUEUED:
                    walk = [
                        TicketState.IN_PROGRESS,
                        TicketState.ABORTED,
                    ]
                elif current == TicketState.IN_PROGRESS:
                    walk = [TicketState.ABORTED]
                elif current == TicketState.DONE:
                    # DONE → QUEUED → IN_PROGRESS → ABORTED
                    walk = [
                        TicketState.QUEUED,
                        TicketState.IN_PROGRESS,
                        TicketState.ABORTED,
                    ]
                for next_state in walk:
                    try:
                        ticket_transition(
                            project_root, ticket_slug, next_state,
                            by=actor, notes=consolidation_notes,
                        )
                    except IllegalTransitionError:
                        break
                if get_ticket_state(project_root, ticket_slug) == TicketState.ABORTED:
                    any_applied = True
            except Exception:  # noqa: BLE001 — best-effort
                continue
        if any_applied:
            applied.append(decision)
    return applied


__all__ = [
    "ConsolidationDecision",
    "find_cross_feature_duplicates",
    "consolidate_cross_feature_duplicates",
]
