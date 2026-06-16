"""Content-level scope-leak detection (M3.75) — T-ab74.

T-ab73 closed the *structural* scope-leak axis: a ticket whose parent
feature belongs to a different milestone is rejected at write time. But
the ldr-final fresh pilot M1 design (2026-06-06) surfaced a *content*
leak that the structural gate can't see — 3 of 23 tickets described M2/M6
work (a ``GET /dashboard`` endpoint returning partner-profile data; a
dashboard skeleton with time/weather/news card placeholders) even though
their parent feature (``session-middleware-and-protected-route-enforcement``)
was legitimately M1. The leak lived in the ticket *prose* authored during
M3 decomposition, not in the structural milestone field.

The discriminator is the ticket **title**: it names the deliverable. A
foreign-milestone surface noun in the title means the ticket *builds* that
surface; the same noun in the body is a legitimate guard/redirect target
(``guard /dashboard route (stub; actual dashboard lands in M3)``). So we
scan titles only — body references stay legitimate.

Foreign-surface tokens are derived structurally from the milestone roster:
tokenize every non-active milestone's slug + name, subtract the active
milestone's own tokens and a generic-stopword set. This mirrors T-ab50's
"explicit signal beats LLM heuristic" pattern — deterministic, no agent
calls.

Action: auto-retract (ABORTED) at the post-design M3.75 hook, sibling to
``cross_feature``. Deliberately NOT a write-time hard reject — T-ab70's
revert (``ffad1cb``) showed in-the-retry-path scope enforcement drives
Rabbit into question loops. Running after the design loop exits keeps this
structurally outside the retry path. The file stays on disk (forensics),
ABORTED is recoverable, and the work isn't lost — it re-decomposes when
that milestone's own design run fires.

Validation (ldr-final M1, 6 tickets touching cross-milestone surfaces):
3/3 leaks flagged, 3/3 legit guard/redirect references cleared.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from wonderland.cross_feature import (
    _build_feature_index,
    _normalize_title_tokens,
    _parse_ticket_sources,
    _ticket_parent_feature,
)
from wonderland.feature import FeatureRegistry
from wonderland.milestone import MilestoneRegistry
from wonderland.ticket import TicketRegistry
from wonderland.ticket_lifecycle import (
    IllegalTransitionError,
    TicketState,
    back_fill_state,
    get_state as get_ticket_state,
    transition as ticket_transition,
)

# Generic scaffolding tokens that appear in milestone slugs/names but
# carry no surface-ownership signal — stripping them keeps the foreign
# token set to distinctive domain nouns. ``time`` is included because it
# is too generic to flag on (``session timeout`` tokenizes to ``timeout``,
# not ``time``; the card-family keeps its distinctive ``weather`` / ``news``
# / ``card`` / ``dashboard`` / ``partner`` / ``profile`` tokens).
_SCOPE_STOPWORDS: frozenset[str] = frozenset({
    "foundation", "core", "base", "setup", "integration", "demo",
    "readiness", "management", "support", "storage", "time",
    "milestone", "phase", "and", "the", "for", "with",
})


def _milestone_tokens(slug: str, name: str) -> frozenset[str]:
    """Tokenize a milestone's slug + name into meaningful surface tokens.

    Reuses cross_feature's title tokenizer (lowercase, split on
    non-alphanumeric, drop 1-char + scaffolding stopwords) then strips
    a leading ``mNN`` order prefix (``m1``, ``m12``) and the scope
    stopword set.
    """
    raw = _normalize_title_tokens(f"{slug} {name}")
    return frozenset(
        t for t in raw
        if t not in _SCOPE_STOPWORDS
        and not re.fullmatch(r"m\d+", t)
    )


def _foreign_milestone_tokens(
    project_root: Path, active_slug: str,
) -> dict[str, frozenset[str]]:
    """Map each non-active milestone slug → its distinctive surface tokens.

    A token is dropped from a foreign milestone's set if it also belongs
    to the active milestone (the active milestone legitimately owns it,
    so a ticket naming it is in-scope). Returns ``{}`` when the roster has
    fewer than two milestones (nothing to leak across).
    """
    registry = MilestoneRegistry(project_root)
    milestones = registry.list_milestones()
    if len(milestones) < 2:
        return {}

    active_tokens: frozenset[str] = frozenset()
    foreign_raw: dict[str, frozenset[str]] = {}
    for m in milestones:
        tokens = _milestone_tokens(m.slug, m.name)
        if m.slug == active_slug:
            active_tokens = tokens
        else:
            foreign_raw[m.slug] = tokens

    return {
        slug: tokens - active_tokens
        for slug, tokens in foreign_raw.items()
    }


@dataclass(frozen=True)
class ScopeLeakDecision:
    """One per ticket whose title names a foreign-milestone surface."""

    ticket_slug: str
    title: str
    foreign_tokens: frozenset[str]
    foreign_milestones: tuple[str, ...]

    def summary(self) -> str:
        return (
            f"``{self.ticket_slug}`` (title=``{self.title}``) names "
            f"foreign-milestone surface(s) {sorted(self.foreign_tokens)} "
            f"belonging to {list(self.foreign_milestones)}"
        )


def _ticket_belongs_to_active(
    record, active_slug: str,
    feature_registry: FeatureRegistry, feature_slugs: set[str],
) -> bool:
    """True iff the ticket's parent feature belongs to the active
    milestone. Mirrors T-ab73's ticket -> parent feature -> milestone
    resolution. Conservative: returns False when the parent feature
    or its milestone can't be resolved, so the gate never touches a
    ticket it can't positively attribute to the active scope (this is
    what keeps a later milestone's design run from retracting an
    earlier milestone's tickets — the over-reach T-ab74 v1 had)."""
    try:
        sources = _parse_ticket_sources(record.path.read_text(encoding="utf-8"))
    except OSError:
        return False
    parent_slug = _ticket_parent_feature(sources, feature_slugs)
    if parent_slug is None:
        return False
    parent = feature_registry.find_by_slug(parent_slug)
    if parent is None or not parent.milestone:
        return False
    parent_milestone = (
        parent.milestone.split(":", 1)[1]
        if ":" in parent.milestone
        else parent.milestone
    )
    return parent_milestone == active_slug


def find_content_scope_leaks(
    project_root: Path, active_slug: str,
) -> list[ScopeLeakDecision]:
    """Tickets whose TITLE tokens intersect a foreign milestone's surface
    tokens. Pure read-side; no on-disk mutations.

    Only tickets whose parent feature belongs to the ACTIVE milestone are
    candidates — a ticket parented to an earlier milestone's feature is
    out of this run's purview and must never be retracted (T-ab74 v1
    scanned every ticket on disk, so an M2 design run would have retracted
    M1's auth tickets because 'auth' is a foreign token under M2).

    Returns ``[]`` when there's no active scope signal, a single-milestone
    roster, or no leaking titles.
    """
    if not active_slug:
        return []
    foreign = _foreign_milestone_tokens(project_root, active_slug)
    if not foreign:
        return []

    feature_registry = FeatureRegistry(project_root)
    feature_slugs, _ = _build_feature_index(project_root)

    registry = TicketRegistry(project_root)
    decisions: list[ScopeLeakDecision] = []
    for record in registry.list_tickets():
        if not _ticket_belongs_to_active(
            record, active_slug, feature_registry, feature_slugs
        ):
            continue
        title_tokens = _normalize_title_tokens(record.title)
        if not title_tokens:
            continue
        hit_tokens: set[str] = set()
        hit_milestones: list[str] = []
        for ms_slug, ms_tokens in foreign.items():
            overlap = title_tokens & ms_tokens
            if overlap:
                hit_tokens |= overlap
                hit_milestones.append(ms_slug)
        if hit_tokens:
            decisions.append(ScopeLeakDecision(
                ticket_slug=record.slug,
                title=record.title,
                foreign_tokens=frozenset(hit_tokens),
                foreign_milestones=tuple(sorted(hit_milestones)),
            ))
    return decisions


def retract_content_scope_leaks(
    project_root: Path,
    active_slug: str,
    *,
    actor: str = "wonderland-substrate",
) -> list[ScopeLeakDecision]:
    """Find + auto-retract content scope-leak tickets.

    Each flagged ticket is walked to ``ABORTED`` via ticket_lifecycle
    (PENDING→QUEUED→IN_PROGRESS→ABORTED as needed; DONE routes back
    through QUEUED). The file is LEFT on disk for forensics; ABORTED is
    recoverable (operator un-aborts via the canonical retry path). The
    work re-decomposes when ``active_slug``'s sibling milestone runs its
    own design pass.

    Returns the decisions actually applied (a ticket that fails to reach
    ABORTED is dropped — best-effort, retract-what-we-can).
    """
    decisions = find_content_scope_leaks(project_root, active_slug)
    applied: list[ScopeLeakDecision] = []
    for decision in decisions:
        slug = decision.ticket_slug
        try:
            current = get_ticket_state(project_root, slug)
            if current == TicketState.ABORTED:
                applied.append(decision)
                continue
            if current is None:
                back_fill_state(
                    project_root, slug, TicketState.PENDING,
                    notes="Back-fill for content scope-leak retraction",
                )
                current = TicketState.PENDING

            notes = (
                f"Content scope-leak (T-ab74): title names foreign-"
                f"milestone surface {sorted(decision.foreign_tokens)} "
                f"({list(decision.foreign_milestones)}) under active "
                f"scope {active_slug!r}. Defer to the owning milestone's "
                f"design run."
            )
            walk = {
                TicketState.PENDING: [
                    TicketState.QUEUED,
                    TicketState.IN_PROGRESS,
                    TicketState.ABORTED,
                ],
                TicketState.QUEUED: [
                    TicketState.IN_PROGRESS,
                    TicketState.ABORTED,
                ],
                TicketState.IN_PROGRESS: [TicketState.ABORTED],
                TicketState.DONE: [
                    TicketState.QUEUED,
                    TicketState.IN_PROGRESS,
                    TicketState.ABORTED,
                ],
            }.get(current, [])
            for next_state in walk:
                try:
                    ticket_transition(
                        project_root, slug, next_state,
                        by=actor, notes=notes,
                    )
                except IllegalTransitionError:
                    break
            if get_ticket_state(project_root, slug) == TicketState.ABORTED:
                applied.append(decision)
        except Exception:  # noqa: BLE001 — best-effort
            continue
    return applied


__all__ = [
    "ScopeLeakDecision",
    "find_content_scope_leaks",
    "retract_content_scope_leaks",
]
