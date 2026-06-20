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
_TITLE_RE = re.compile(r"^## Ticket \d+:\s*(.+?)$", re.MULTILINE)

# T-ab63 pass 2: title-similarity threshold for cross-feature
# consolidation. ldr-final M1 design shipped 5 schema tickets / 5
# hashing tickets / 5 session-middleware tickets across 5 different
# features — exact-upstream-source clustering missed them because
# each was decomposed from a different feature's stories. Title
# tokens overlap ≥0.5 Jaccard on these obvious dups after aggressive
# normalization. Threshold of 0.65 to avoid false positives on
# tickets like "test signup endpoint" + "test signin endpoint"
# where 3 of 4 tokens overlap but the work is legitimately distinct.
_TITLE_SIMILARITY_THRESHOLD: float = 0.65

# Stopwords stripped from title tokens before computing similarity —
# these are scaffolding words that appear across most tickets and
# would inflate similarity scores without signaling actual overlap.
_TITLE_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "and", "or", "the", "to", "for", "with", "in", "on",
    "of", "via", "by", "from", "into", "as", "is", "be", "this", "that",
    # Substrate-conventional words that show up everywhere:
    "implement", "add", "create", "define", "setup", "set", "up", "configure",
})


def _normalize_title_tokens(title: str) -> frozenset[str]:
    """Lower-case + tokenize a ticket title, strip stopwords.
    Returns a frozenset of meaningful tokens for Jaccard similarity.

    Tokenization: split on non-alphanumeric, lowercase, filter
    stopwords and 1-char tokens. Punctuation stripped. Preserves
    technical terms like ``passlib``, ``sqlite``, ``api/signup``."""
    # Split on non-alphanumeric (handles slashes in /api/signup,
    # hyphens, colons in section headers, etc.)
    raw_tokens = re.split(r"[^a-z0-9_]+", title.lower())
    return frozenset(
        t for t in raw_tokens
        if len(t) > 1 and t not in _TITLE_STOPWORDS
    )


def _title_jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Jaccard similarity between two token sets. 0 when either empty."""
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union) if union else 0.0


def _parse_ticket_title(ticket_md: str) -> str:
    """Extract the H2 title text from a ticket markdown.

    Returns empty string when no H2 is found (malformed file)."""
    m = _TITLE_RE.search(ticket_md)
    return m.group(1).strip() if m else ""


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

    # ticket_slug → surface signature. The surface-agreement GUARD: a
    # cross-feature merge (Pass 1 upstream-source OR Pass 2 title-Jaccard)
    # is only valid between tickets that build the SAME surface. The
    # M1-verify run exposed why: 15 tickets all cited the one story
    # ``kohl-can-sign-up...`` as upstream, so Pass 1 clustered them and
    # aborted 14 — but they were signup, signin, /auth/me, schema, and
    # both frontend forms (all DIFFERENT surfaces). One story legitimately
    # decomposes into many surfaces; "same upstream" ≠ "duplicate." The
    # same convergent lesson as everywhere else: only the surface
    # signature is a safe merge key. (None==None still merges — two
    # un-surfaced tickets sharing upstream are the original Pass 1 case.)
    ticket_surface: dict[str, str | None] = {
        r.slug: _surface_signature(r.title) for r in tickets
    }

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

    # ---- Pass 1: cluster by EXACT upstream source set (T-a5) ----
    # Cluster: upstream_set → list[(ticket_slug, parent_feature)]
    clusters: dict[frozenset[str], list[tuple[str, str]]] = defaultdict(list)
    for ticket_slug, (parent, upstream) in ticket_info.items():
        clusters[upstream].append((ticket_slug, parent))

    decisions: list[ConsolidationDecision] = []
    consolidated_slugs: set[str] = set()
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
        winner_surface = ticket_surface.get(winner_slug)
        # Surface-agreement guard: only retract members that build the
        # SAME surface as the winner. Different-surface members sharing
        # this upstream set are distinct deliverables — leave them
        # standing (their own same-surface dups, if any, are caught by
        # the surface pass).
        retracted = tuple(
            slug for _score, slug, _parent in scored[1:]
            if ticket_surface.get(slug) == winner_surface
        )
        if not retracted:
            continue
        decisions.append(ConsolidationDecision(
            kept_slug=winner_slug,
            kept_parent_feature=winner_parent,
            retracted_slugs=retracted,
            upstream_sources=upstream,
        ))
        consolidated_slugs.add(winner_slug)
        consolidated_slugs.update(retracted)

    # ---- Pass 2: cluster by title-TOKEN Jaccard similarity (T-ab63 pass 2) ----
    # ldr-final M1 design shipped 31 tickets where ~25 were near-
    # duplicates with DIFFERENT upstream sources (each feature's M3
    # decomposed from its own stories, but the resulting tickets
    # described the same component — 5 schema tickets, 5 hashing
    # tickets, 5 session-middleware tickets). Pass 1's exact-source
    # clustering missed them entirely. Pass 2 catches them via title-
    # token Jaccard ≥ _TITLE_SIMILARITY_THRESHOLD across different
    # parent features.
    #
    # Skips tickets already consolidated by Pass 1 (no double-jeopardy).
    # Each Pass 2 cluster: ≥2 tickets, ≥2 distinct parents, all-pairs
    # Jaccard ≥ threshold (transitive closure of pairwise threshold
    # ensures no chain-of-weak-links cluster).
    titles: dict[str, tuple[str, frozenset[str]]] = {}  # slug → (parent, tokens)
    for record in tickets:
        if record.slug in consolidated_slugs:
            continue
        if record.slug not in ticket_info:
            # Either orphan (no parent) or ticket_info skipped it
            # earlier — re-read parent and title here.
            try:
                text = record.path.read_text(encoding="utf-8")
            except OSError:
                continue
            sources = _parse_ticket_sources(text)
            parent = _ticket_parent_feature(sources, feature_slugs)
            if parent is None:
                continue
            title_text = _parse_ticket_title(text)
        else:
            parent, _upstream = ticket_info[record.slug]
            try:
                text = record.path.read_text(encoding="utf-8")
            except OSError:
                continue
            title_text = _parse_ticket_title(text)
        tokens = _normalize_title_tokens(title_text)
        if len(tokens) < 2:
            # Title too short / generic to cluster on
            continue
        titles[record.slug] = (parent, tokens)

    # Greedy clustering: walk slugs in registry order, for each
    # unassigned slug, find all OTHER unassigned slugs with Jaccard
    # ≥ threshold against it. That's the cluster seed.
    assigned: set[str] = set()
    title_slugs_ordered = list(titles.keys())  # registry-stable order
    for seed_slug in title_slugs_ordered:
        if seed_slug in assigned:
            continue
        seed_parent, seed_tokens = titles[seed_slug]
        cluster_members: list[tuple[str, str, frozenset[str]]] = [
            (seed_slug, seed_parent, seed_tokens)
        ]
        for cand_slug in title_slugs_ordered:
            if cand_slug == seed_slug or cand_slug in assigned:
                continue
            cand_parent, cand_tokens = titles[cand_slug]
            if _title_jaccard(seed_tokens, cand_tokens) >= _TITLE_SIMILARITY_THRESHOLD:
                cluster_members.append((cand_slug, cand_parent, cand_tokens))
        if len(cluster_members) < 2:
            continue
        cluster_parents = {p for _slug, p, _toks in cluster_members}
        if len(cluster_parents) < 2:
            # All in same feature — M3.5 within-feature consolidation
            # was supposed to handle this. We could surface it but
            # the current contract is cross-feature only.
            continue
        # Mark all assigned
        for slug, _p, _t in cluster_members:
            assigned.add(slug)
        # Pick winner: longest title (most-specific) wins; tie-break
        # by alphabetical slug for determinism.
        cluster_members.sort(
            key=lambda x: (-len(x[2]), x[0])
        )
        winner_slug, winner_parent, winner_tokens = cluster_members[0]
        winner_surface = ticket_surface.get(winner_slug)
        # Surface-agreement guard (same as Pass 1): only retract members
        # that build the same surface as the winner.
        retracted = tuple(
            slug for slug, _p, _t in cluster_members[1:]
            if ticket_surface.get(slug) == winner_surface
        )
        if not retracted:
            continue
        # Build a synthetic "upstream sources" for the cluster: union
        # of all members' upstream sets. Used by the ConsolidationDecision
        # for audit / forensics, not for the cluster-identification.
        synthetic_upstream: frozenset[str] = frozenset()
        for slug, _p, _t in cluster_members:
            if slug in ticket_info:
                _parent, upstream = ticket_info[slug]
                synthetic_upstream = synthetic_upstream | upstream
        decisions.append(ConsolidationDecision(
            kept_slug=winner_slug,
            kept_parent_feature=winner_parent,
            retracted_slugs=retracted,
            upstream_sources=synthetic_upstream,
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


# ---- Within-feature dedup (T-ab79) — surface signatures, not Jaccard ----
# The M1-forced design pass shipped 13 tickets for ONE feature, ~5 reworded
# dup pairs (two decomposition rotations over the same feature; M3.5 agent
# consolidation missed them). Title-token Jaccard provably CANNOT separate
# these: distinct signup-vs-signin frontend tickets score 1.00 (the
# tokenizer eats sign-"up"/"in"), while a real session-middleware dup scores
# 0.20. The discriminator is the SURFACE a ticket builds — its endpoint
# path, or its UI action — not lexical overlap. Two tickets under the same
# feature are dups iff they target the same surface. Layer (fe/be) is part
# of the signature so a frontend form and its backend endpoint never merge.
_PATH_RE = re.compile(r"/[a-z][a-z0-9/_{}-]*")
_FE_RE = re.compile(
    r"\b(frontend|react|vite|ui|page|screen|component|form|route)\b"
)
# Ordered: first match wins. signup before signin so "sign-up" can't fall
# through to a looser pattern. Each pattern is distinctive enough that a
# signup ticket never matches the signin action and vice-versa.
# NOT a catalog of known surfaces. The generic domain-noun fallback below
# (_surface_signature) handles unknown domains — adding ``roster`` or
# ``championship`` here would be redundant. This list is ONLY for surfaces
# the generic first-salient-noun heuristic gets WRONG, of which there are
# three kinds:
#   1. Shared-noun confusables the tokenizer can't split — signup/signin both
#      fall to noun:``sign`` (the up/in is eaten) and would false-merge. The
#      explicit actions keep them distinct.
#   2. Surface named by a non-surface-shape word the gate drops — ``schema``
#      (a "Create SQLite schema" ticket has no page/card/endpoint word, so the
#      fallback returns None; and its first noun would be ``sqlite``).
#   3. Surface named by a NON-FIRST noun — ``profile`` ("Wrestler profile page"
#      → fallback picks ``wrestler``, lumping profile with wrestler-list/edit;
#      the explicit action keys it on the precise surface).
# GUARDRAIL: before adding an entry, check the fallback first. If it already
# yields a correct, distinct noun for your surface (it does for roster, faction,
# weather/news cards, dashboard — all pruned T-ab80), DON'T add it here.
_SURFACE_ACTIONS: tuple[tuple[str, str], ...] = (
    ("signup", r"sign[\s_-]?up|signup|registration|register"),
    ("signin", r"sign[\s_-]?in|signin|log[\s_-]?in|login"),
    ("signout", r"sign[\s_-]?out|log[\s_-]?out|logout"),
    ("session-middleware", r"session middleware|middleware"),
    ("schema", r"\bschema\b|migration|\btable\b"),
    ("profile", r"profile"),
)


# Tokens stripped when deriving the generic domain-noun fallback below.
# These are the layer/qualifier/scaffolding words that lead a title without
# naming its SUBJECT — we want the first word that names the entity/surface
# (``roster``, ``faction``, ``championship``), not ``frontend`` / ``public`` /
# ``page``. Reuses the title stopwords + the layer vocabulary + the
# admin/public scoping qualifiers + page-shape nouns.
_SURFACE_SKIP_TOKENS: frozenset[str] = _TITLE_STOPWORDS | frozenset({
    "frontend", "backend", "react", "vite", "ui", "page", "screen",
    "component", "form", "route", "layout", "view",
    "public", "admin", "private", "api", "endpoint", "endpoints",
    "get", "post", "put", "patch", "delete",
})

# The generic noun fallback fires ONLY when the title names a SURFACE shape —
# a UI surface (page/card/banner/…) or an explicit endpoint. This is the gate
# that keeps infra/config tickets (``Set up Vite proxy and CORS config``)
# signing None (never deduped) while letting domain pages (``Roster discovery
# page``) bucket. Without it, the fallback would tag every path-less ticket
# with a noun and pull setup/config work into dedup clusters it doesn't belong
# in.
_SURFACE_SHAPE_RE = re.compile(
    r"\b(page|screen|view|list|listing|detail|banner|card|table|modal|"
    r"menu|sidebar|navbar|panel|grid|component|form|endpoint|endpoints|"
    r"dashboard)\b"
)


def _surface_signature(title: str) -> str | None:
    """The surface a ticket builds — ``<layer>|path:<endpoint>`` (strongest,
    generic), ``<layer>|act:<action>`` (known-action whitelist), or
    ``<layer>|noun:<entity>`` (generic domain-noun fallback). Returns None
    only when nothing nameable is derivable (→ never deduped; conservative).

    Layer (fe/be) is encoded so a frontend form and its backend endpoint —
    or two frontend pages for different actions — keep distinct signatures.
    """
    t = title.lower()
    layer = "fe" if _FE_RE.search(t) else "be"
    m = _PATH_RE.search(t)
    if m:
        path = m.group(0).rstrip("/")
        if len(path) > 2:  # skip a bare "/" or single-char noise
            return f"{layer}|path:{path}"
    for name, pattern in _SURFACE_ACTIONS:
        if re.search(pattern, t):
            return f"{layer}|act:{name}"
    # Generic domain-noun fallback (T-ab80). The action whitelist above only
    # knows surfaces seen in PRIOR pilots (auth signup/signin, ldr weather/
    # news cards, dashboard/schema/profile). A NEW domain's surfaces match
    # nothing and sign None → never dedup → the same page gets built N times.
    # wwu M2 receipt: three "Roster discovery page" tickets all signed None
    # and all shipped (vs the profile tickets, which matched ``profile`` and
    # deduped cleanly). Bucketing by the title's first SALIENT noun
    # generalizes to any domain — ``roster``, ``faction``, ``championship`` —
    # without a hand-maintained list. This only COARSE-buckets; the
    # same-surface title-Jaccard sub-cluster (_SAME_SURFACE_TITLE_THRESHOLD)
    # still does the fine merge decision, so a coarse bucket can't over-merge
    # distinct responsibilities (the serve-HTML vs serve-data /dashboard case
    # the threshold was calibrated on still holds). Gated on a surface-shape
    # word so config/infra tickets keep signing None.
    if _SURFACE_SHAPE_RE.search(t):
        for tok in re.split(r"[^a-z0-9_]+", t):
            if len(tok) > 1 and tok not in _SURFACE_SKIP_TOKENS:
                return f"{layer}|noun:{tok}"
    return None


# A surface signature alone is too coarse to merge on: one endpoint PATH
# legitimately spawns several complementary tickets — serve the SPA shell,
# return the JSON data, wire the session middleware — that all sign as
# ``be|path:/dashboard``. Merging them eats the substantive ones (the data
# endpoint) and keeps the trivial one (the HTML shell), which is how a
# feature ends up with components that have no data to render. So WITHIN a
# surface group we additionally require title similarity: two same-surface
# tickets merge only if they describe the same RESPONSIBILITY, not just the
# same path. Calibrated on ldr-ophanic M2: the four /dashboard tickets
# (serve / data / weather / middleware) score 0.07–0.25 pairwise; genuine
# reworded dups score 0.75+. Bias is deliberately toward NOT merging — a
# surviving duplicate is recoverable, a culled data endpoint is a hollow
# build.
_SAME_SURFACE_TITLE_THRESHOLD = 0.30


def _subcluster_by_title(
    members: list[tuple[str, str, str | None]], threshold: float,
) -> list[list[tuple[str, str, str | None]]]:
    """Partition a same-surface group into clusters of title-similar tickets
    (transitive closure of pairwise title-Jaccard ≥ threshold). Only members
    of the same cluster are treated as duplicates of each other."""
    n = len(members)
    tokens = [_normalize_title_tokens(m[1]) for m in members]
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _title_jaccard(tokens[i], tokens[j]) >= threshold:
                parent[find(i)] = find(j)

    clusters: dict[int, list[tuple[str, str, str | None]]] = defaultdict(list)
    for i, m in enumerate(members):
        clusters[find(i)].append(m)
    return list(clusters.values())


def find_surface_duplicates(
    project_root: Path,
) -> list[ConsolidationDecision]:
    """Tickets that build the same surface — grouped by surface signature
    AND title-responsibility, across feature boundaries AND including
    orphaned tickets (no resolvable parent). Pure read-side.

    Unification (T-ab79 follow-up): the M1-fullstack run showed surface
    dups leaking three ways — within a feature, across two features, and
    via orphaned tickets citing a story slug. Title-Jaccard (cross-feature
    T-ab63 pass 2) and parent-scoped grouping (the original within-feature
    pass) each only caught one slice. Grouping by surface signature alone
    catches all three at once: any surface appearing on ≥2 tickets is a
    duplicate, no matter which feature claims them or whether they're
    attributed at all.

    Winner selection prefers a PARENTED ticket over an orphan (so the
    survivor has a home), then the longest/most-specific title, then alpha
    slug for determinism."""
    registry = TicketRegistry(project_root)
    tickets = registry.list_tickets()
    if not tickets:
        return []
    feature_slugs, _ = _build_feature_index(project_root)

    # surface_signature → [(slug, title, parent_or_None)]
    groups: dict[str, list[tuple[str, str, str | None]]] = defaultdict(list)
    for record in tickets:
        # Skip tickets a prior pass already aborted — otherwise this pass
        # re-clusters a dead ticket with its live sibling, picks the dead
        # one as winner, and aborts the survivor (both end up aborted).
        if get_ticket_state(project_root, record.slug) == TicketState.ABORTED:
            continue
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            continue
        sig = _surface_signature(record.title)
        if sig is None:
            continue
        parent = _ticket_parent_feature(
            _parse_ticket_sources(text), feature_slugs
        )
        groups[sig].append((record.slug, record.title, parent))

    decisions: list[ConsolidationDecision] = []
    for sig, members in groups.items():
        if len(members) < 2:
            continue
        # Same surface is necessary but NOT sufficient — sub-cluster by
        # title so only same-responsibility tickets merge (serve-HTML and
        # serve-data on /dashboard stay distinct).
        for cluster in _subcluster_by_title(
            members, _SAME_SURFACE_TITLE_THRESHOLD
        ):
            if len(cluster) < 2:
                continue
            # Prefer parented (parent not None) → longest title → alpha slug.
            cluster.sort(key=lambda m: (m[2] is None, -len(m[1]), m[0]))
            winner_slug, _wtitle, winner_parent = cluster[0]
            retracted = tuple(slug for slug, _t, _p in cluster[1:])
            decisions.append(ConsolidationDecision(
                kept_slug=winner_slug,
                kept_parent_feature=winner_parent or "(orphan)",
                retracted_slugs=retracted,
                upstream_sources=frozenset({sig}),
            ))
    return decisions


# Back-compat alias — the original name from the within-feature-only pass.
find_within_feature_duplicates = find_surface_duplicates


def consolidate_surface_duplicates(
    project_root: Path,
    *,
    actor: str = "wonderland-substrate",
) -> list[ConsolidationDecision]:
    """Find + apply surface dedup (within + cross feature + orphans).
    Retracted tickets transition to ABORTED (file left on disk for
    forensics); recoverable, best-effort — same as the sibling passes."""
    decisions = find_surface_duplicates(project_root)
    applied: list[ConsolidationDecision] = []
    for decision in decisions:
        any_applied = False
        for ticket_slug in decision.retracted_slugs:
            if _abort_ticket_as_duplicate(
                project_root, ticket_slug,
                kept_slug=decision.kept_slug,
                kept_parent=decision.kept_parent_feature,
                actor=actor,
            ):
                any_applied = True
        if any_applied:
            applied.append(decision)
    return applied


# Back-compat alias — the original name from the within-feature-only pass.
consolidate_within_feature_duplicates = consolidate_surface_duplicates


def _abort_ticket_as_duplicate(
    project_root: Path, ticket_slug: str, *,
    kept_slug: str, kept_parent: str, actor: str,
) -> bool:
    """Walk a duplicate ticket to ABORTED via ticket_lifecycle. Returns
    True iff it ends in ABORTED. Mirrors the abort path in
    ``consolidate_cross_feature_duplicates``."""
    try:
        current = get_ticket_state(project_root, ticket_slug)
        if current == TicketState.ABORTED:
            return True
        notes = (
            f"Within-feature consolidation: duplicate surface of "
            f"{kept_slug!r} under feature {kept_parent!r}"
        )
        if current is None:
            back_fill_state(
                project_root, ticket_slug, TicketState.IN_PROGRESS,
                notes="Back-fill to in_progress for within-feature abort",
            )
            current = TicketState.IN_PROGRESS
        walk = {
            TicketState.PENDING: [
                TicketState.QUEUED, TicketState.IN_PROGRESS,
                TicketState.ABORTED,
            ],
            TicketState.QUEUED: [
                TicketState.IN_PROGRESS, TicketState.ABORTED,
            ],
            TicketState.IN_PROGRESS: [TicketState.ABORTED],
            TicketState.DONE: [
                TicketState.QUEUED, TicketState.IN_PROGRESS,
                TicketState.ABORTED,
            ],
        }.get(current, [])
        for next_state in walk:
            try:
                ticket_transition(
                    project_root, ticket_slug, next_state,
                    by=actor, notes=notes,
                )
            except IllegalTransitionError:
                break
        return get_ticket_state(project_root, ticket_slug) == TicketState.ABORTED
    except Exception:  # noqa: BLE001 — best-effort
        return False


def reattribute_orphaned_tickets(
    project_root: Path,
    active_slug: str | None = None,
    *,
    min_jaccard: float = 0.15,
) -> list[tuple[str, str, float]]:
    """Re-home tickets that cite no resolvable parent feature to the
    feature whose title best matches the ticket's title.

    T-ab78: M2 design's parallel decomposition left 4 of 13 tickets
    citing the milestone ``guid:slug`` as ``sources[0]`` instead of a
    feature — the thread-scoped attribution
    (``_attribute_ticket_sources_to_iteration_feature``) skipped them on
    ``scoped=0`` threads — and the geocoding-resolver feature got 0
    tickets (its work mis-injected into the schema feature). Orphaned
    tickets are invisible to BOTH cross-feature dedup (needs >=2 FEATURE
    parents) and M3.5 within-feature consolidation, so the duplicates
    they represent never get collapsed. Re-attaching them by title
    similarity feeds correct input to the dedup that runs next.

    When ``active_slug`` is given, only features belonging to that
    milestone are candidates (``feature.milestone``, reliable since
    T-ab76) — an M2 orphan never re-homes to an M1 feature.

    Deterministic; mirrors the title-token machinery used by T-ab63
    pass 2. Mutates the ticket's on-disk ``**Sources:**`` line.

    Returns ``[(ticket_slug, feature_slug, jaccard)]`` for each
    re-attached ticket.
    """
    feature_slugs, _ = _build_feature_index(project_root)
    if not feature_slugs:
        return []

    feature_registry = FeatureRegistry(project_root)
    candidates: dict[str, frozenset[str]] = {}
    for slug in feature_slugs:
        if active_slug is not None:
            rec = feature_registry.find_by_slug(slug)
            ms = None
            if rec is not None and rec.milestone:
                ms = (
                    rec.milestone.split(":", 1)[1]
                    if ":" in rec.milestone
                    else rec.milestone
                )
            if ms != active_slug:
                continue
        # Feature slug -> title tokens (slug is hyphenated title).
        candidates[slug] = _normalize_title_tokens(slug.replace("-", " "))
    if not candidates:
        return []

    registry = TicketRegistry(project_root)
    all_tickets = registry.list_tickets()

    # Surface-owner index: which candidate feature already owns each
    # surface (from its PARENTED tickets). The unification's primary
    # re-attribution signal — title↔feature-slug Jaccard is unreliable
    # when feature slugs are verbose user-story phrases
    # (``kohl-signs-up-with-email-and-password``) and ticket titles are
    # technical (``POST /auth/signup``). The surface a ticket builds is
    # the robust signal: an orphaned ``POST /auth/signup`` belongs to
    # whichever feature already has a parented ``/auth/signup`` ticket.
    surface_owner: dict[str, str] = {}
    for record in all_tickets:
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            continue
        parent = _ticket_parent_feature(
            _parse_ticket_sources(text), feature_slugs
        )
        if parent is None or parent not in candidates:
            continue
        sig = _surface_signature(record.title)
        if sig is not None:
            surface_owner.setdefault(sig, parent)

    reattached: list[tuple[str, str, float]] = []
    for record in all_tickets:
        try:
            text = record.path.read_text(encoding="utf-8")
        except OSError:
            continue
        sources = _parse_ticket_sources(text)
        if _ticket_parent_feature(sources, feature_slugs) is not None:
            continue  # already has a resolvable feature parent

        # Primary: surface-owner match. Fallback: title↔slug Jaccard, but
        # surface-GATED — a candidate feature whose own surface (read off its
        # slug) conflicts with the orphan's surface can't own it, so it's
        # excluded from the fuzzy match. This is what stops an M4 news-card
        # orphan ("News card: frontend rendering…") from Jaccard-matching the
        # M3 weather feature on generic {card, cached} tokens: weathercard ≠
        # newscard, so the weather feature is ineligible and the news ticket
        # stays orphaned for its own milestone. Surface-LESS orphans (and
        # surface-less candidates) keep the original token-Jaccard behaviour.
        best_slug: str | None = None
        best_score = 0.0
        sig = _surface_signature(record.title)
        if sig is not None and sig in surface_owner:
            best_slug, best_score = surface_owner[sig], 1.0
        else:
            title_tokens = _normalize_title_tokens(record.title)
            if not title_tokens:
                continue
            sig_surface = sig.split("|", 1)[1] if sig else None
            for fslug, ftokens in candidates.items():
                if sig_surface is not None:
                    fsig = _surface_signature(fslug.replace("-", " "))
                    # Compare the surface part only (act:/path:), not the
                    # fe/be layer — a feature slug rarely encodes layer.
                    if fsig is not None and fsig.split("|", 1)[1] != sig_surface:
                        continue  # feature owns a different surface
                score = _title_jaccard(title_tokens, ftokens)
                if score > best_score:
                    best_slug, best_score = fslug, score
            if best_slug is None or best_score < min_jaccard:
                continue
        m = _SOURCES_RE.search(text)
        if m is None:
            continue
        existing = [s.strip() for s in m.group(1).split(",") if s.strip()]
        new_content = ", ".join([best_slug] + existing)
        # Replace only the captured content span; preserves the exact
        # ``**Sources:**`` prefix.
        new_text = text[: m.start(1)] + new_content + text[m.end(1):]
        try:
            record.path.write_text(new_text, encoding="utf-8")
        except OSError:
            continue
        reattached.append((record.slug, best_slug, best_score))
    return reattached


__all__ = [
    "ConsolidationDecision",
    "find_cross_feature_duplicates",
    "consolidate_cross_feature_duplicates",
    "reattribute_orphaned_tickets",
    "find_surface_duplicates",
    "consolidate_surface_duplicates",
    # Back-compat aliases (within-feature-only era):
    "find_within_feature_duplicates",
    "consolidate_within_feature_duplicates",
]
