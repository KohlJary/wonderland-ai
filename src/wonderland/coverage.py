"""Coverage checks — substrate primitives that detect gaps between
discovered requirements + the artifacts agents have produced (P15 T-m8).

Coverage is a closed-loop concern: a workflow phase can declare
``coverage_check: <name>`` and the runtime will, at end of each
rotation, compute whether the named gap exists. If it does, the
substrate injects a synthetic Dodo observation surfacing the gap +
extends the phase's rotation budget so agents can revise. When the
gap closes, the phase terminates normally.

This module owns the registry of checks + the helpers that compute
them. Substrate integration lives in ``meeting.py`` (the rotation-
end hook) and ``workflow.py`` (the ``PhaseSpec.coverage_check``
field). The checks themselves are pure: they read the project
filesystem + return a structured ``CoverageGap`` (or ``None`` when
coverage is complete).

Two checks ship in v1:

  - ``requirement_coverage`` — every "decomposable" requirement
    appears in some milestone's ``consumes_requirements`` list.
    Personas, out-of-scope, and deal-breakers are exempt: they're
    background context, not buildable units. Used by the
    milestone-plan workflow to drive the planning loop until full
    coverage.

  - ``milestone_realization`` — within a single milestone's design
    run, every consumed requirement is realized by at least one
    feature (via the story-level ``realizes_requirements`` linkage
    added in T-m8b). Used by tdd-design's M2.

New checks plug in by registering a callable in ``_CHECK_REGISTRY``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# Requirement kinds that are NOT expected to live in a milestone's
# consumes_requirements list. These are cross-cutting / context-only
# / explicitly-not-building, so demanding they appear in a milestone
# would create false orphans.
_NON_DECOMPOSABLE_REQUIREMENT_KINDS: frozenset[str] = frozenset(
    {
        "persona",          # WHO uses the system — informs stories, not built
        "situation",        # context for personas (WHEN they reach for the app) — also background
        "out_of_scope",     # explicitly NOT v1
        "deal_breaker",     # would make the project fail — not a feature
    }
)

# Requirement kinds that CAN be consumed by a milestone (so they're
# decomposable in the orphan-check sense — operator should acknowledge
# them in some milestone) but DON'T need to be realized by a feature
# (they're meta-statements about the system, not buildable units).
# Mvp-demo wedge fixes:
#   - ``scope`` / ``constraint`` (round 1): requirements like "v1 has
#     no auth" and "backend availability is hard" kept generating
#     phantom coverage gaps because they're consumed but unbuildable.
#   - ``success_criterion`` (round 2, mvp-demo M4): requirements like
#     "v1 ships when developer can clone-run in 5 minutes" are
#     measurable outcome statements — operator-validated, not feature-
#     realized. Same wedge shape: M4 design got stories but couldn't
#     compose features because Dodo flagged the success_criterion as
#     unrealized. Added here to the realizable-but-not-buildable set.
# All kept in the orphan check (operator should acknowledge them in
# some milestone), just exempt from "needs a feature to realize."
_NON_REALIZABLE_REQUIREMENT_KINDS: frozenset[str] = (
    _NON_DECOMPOSABLE_REQUIREMENT_KINDS | frozenset(
        {
            "scope",              # boundary statement — describes what's IN scope as a constraint, not a buildable feature
            "constraint",         # property the system must have — not a feature, just a true statement about the deliverable
            "success_criterion",  # measurable outcome statement (e.g., "v1 ships when X") — operator-validated, not feature-realized
        }
    )
)


@dataclass(frozen=True)
class CoverageGap:
    """Structured description of a coverage gap. Substrate hands this
    to the nudge-injector to format the synthetic Dodo observation.

    ``check_name``: the registered check that produced this gap (e.g.
        ``requirement_coverage``).
    ``gap_kind``: which side of the gap is short — typically
        ``orphan_requirements``, ``unrealized_requirements``,
        ``phantom_consumes``, etc.
    ``items``: the slugs (or other identifiers) of the missing
        coverage targets.
    ``summary``: human-readable one-liner the substrate can drop into
        a nudge utterance verbatim.
    """

    check_name: str
    gap_kind: str
    items: tuple[str, ...]
    summary: str


# ---------------------------------------------------------------------- #
# Markdown parser — shared with workflow._parse_milestone_body but
# reproduced here so coverage.py doesn't import workflow.py (which
# would create a cycle: workflow.py wants to call into coverage).
# ---------------------------------------------------------------------- #


_KIND_LINE = re.compile(r"^\*\*Kind:\*\*\s*(\S+)", re.MULTILINE)


def _parse_requirement_kind(text: str) -> str | None:
    """Pull the ``**Kind:**`` value out of a requirement markdown.
    Returns the lowercase kind string or None when missing."""
    m = _KIND_LINE.search(text)
    if not m:
        return None
    return m.group(1).strip().lower()


_AXIS_LINE = re.compile(r"^\*\*Axis:\*\*\s*(\S+)", re.MULTILINE)


def _parse_requirement_axis(text: str) -> str | None:
    """T-ab15 — pull the ``**Axis:**`` value out of a requirement
    markdown. Returns the lowercase axis string or None when
    missing (legacy pre-axis requirement). Caller treats None as
    ``both`` for permissive back-compat."""
    m = _AXIS_LINE.search(text)
    if not m:
        return None
    return m.group(1).strip().lower()


def _parse_milestone_consumes(text: str) -> list[str]:
    """Pull the ``**Consumes requirements:**`` bullet list out of a
    milestone markdown. Tolerant of operator hand-edits — same shape
    as the workflow._parse_milestone_body parser, just narrowed to
    the consumes section."""
    return _parse_bullet_section(text, "**Consumes requirements:**")


def _parse_milestone_done_when(text: str) -> list[str]:
    """Pull the ``**Done when:**`` bullet list out of a milestone
    markdown. Used by the done_when_coverage check (tdd-design-no-
    stories A/B variant) where done-when items stand in for the
    story layer as the seed corpus for feature composition."""
    return _parse_bullet_section(text, "**Done when:**")


def _parse_story_realizes(text: str) -> list[str]:
    """Pull the ``**Realizes requirements:**`` bullet list out of a
    story markdown. The renderer emits ``- —`` sentinel when the
    list is empty; treat it as an empty list."""
    items = _parse_bullet_section(text, "**Realizes requirements:**")
    return [s for s in items if s and s != "—" and s != "-"]


def _parse_feature_sources(text: str) -> list[str]:
    """Pull the ``**Sources:**`` line out of a feature markdown.
    Features render sources as a single comma-separated line (not
    bullet list), so the parser is a one-liner extractor."""
    sources_re = re.compile(r"^\*\*Sources?:\*\*\s*(.+?)$", re.MULTILINE)
    m = sources_re.search(text)
    if not m:
        return []
    line = m.group(1).strip()
    if line in ("", "—", "-"):
        return []
    return [s.strip() for s in line.split(",") if s.strip()]


def _parse_feature_milestone(text: str) -> str | None:
    """Pull the ``**Milestone:**`` line out of a feature markdown
    (T-ab5 explicit attribution). Returns the slug (or guid:slug)
    when set; None for legacy features without the field or when
    set to the placeholder dash."""
    return _parse_milestone_field(text)


def _parse_story_milestone(text: str) -> str | None:
    """Pull the ``**Milestone:**`` line out of a story markdown
    (T-ab7 explicit attribution, mirror of feature.milestone).
    Returns the slug (or guid:slug) when set; None for legacy
    stories without the field or when set to the placeholder dash."""
    return _parse_milestone_field(text)


def _parse_milestone_field(text: str) -> str | None:
    """Shared parser for the ``**Milestone:**`` line. Story + feature
    use the same shape; the helper keeps the rendering/parsing
    contracts symmetric."""
    milestone_re = re.compile(r"^\*\*Milestone:\*\*\s*(.+?)$", re.MULTILINE)
    m = milestone_re.search(text)
    if not m:
        return None
    val = m.group(1).strip()
    if val in ("", "—", "-"):
        return None
    return val


def _parse_bullet_section(text: str, header: str) -> list[str]:
    """Pull bullet entries from a named markdown section. Stops at
    the next ``**Section:**`` header or EOF. Tolerates operator
    formatting drift."""
    lines = text.splitlines()
    items: list[str] = []
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped == header:
            in_section = True
            continue
        if stripped.startswith("**") and stripped.endswith(":**"):
            if in_section:
                break
            continue
        if in_section and stripped.startswith("- "):
            items.append(stripped[2:].strip())
    return items


# ---------------------------------------------------------------------- #
# Check 1: requirement_coverage
# ---------------------------------------------------------------------- #


def compute_orphan_requirements(project_root: Path) -> CoverageGap | None:
    """Find decomposable requirements that aren't in any milestone's
    ``consumes_requirements`` list. Returns ``None`` when coverage is
    complete; a CoverageGap with the orphan slugs otherwise.

    A requirement is **decomposable** when its kind is something a
    milestone could plausibly own: situation, scope,
    success_criterion, integration, or constraint. Personas,
    out-of-scope flags, and deal-breakers are exempt.
    """
    req_root = project_root / ".wonderland" / "requirements"
    milestone_root = project_root / ".wonderland" / "milestones"

    if not req_root.is_dir():
        # No requirements at all — no coverage to check.
        return None

    # Collect decomposable requirement slugs by reading each file's
    # Kind line. T-g3 filename: requirement-<short_guid|legacy>-<slug>.md
    decomposable: set[str] = set()
    filename_re = re.compile(
        r"requirement-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
    )
    for path in req_root.glob("requirement-*.md"):
        m = filename_re.match(path.name)
        if not m:
            continue
        slug = m.group(1)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        kind = _parse_requirement_kind(text)
        if kind is None:
            # Kind missing — treat as decomposable conservatively so
            # the operator notices (better false positive than silent
            # skip).
            decomposable.add(slug)
            continue
        if kind in _NON_DECOMPOSABLE_REQUIREMENT_KINDS:
            continue
        decomposable.add(slug)

    if not decomposable:
        return None

    # Union of every milestone's consumes_requirements.
    consumed: set[str] = set()
    if milestone_root.is_dir():
        for path in milestone_root.glob("milestone-*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for slug in _parse_milestone_consumes(text):
                consumed.add(slug)

    orphans = sorted(decomposable - consumed)
    if not orphans:
        return None

    summary = (
        f"Coverage gap: {len(orphans)} requirement(s) are not "
        f"consumed by any milestone — {', '.join(orphans[:5])}"
        + (f", + {len(orphans) - 5} more" if len(orphans) > 5 else "")
    )
    return CoverageGap(
        check_name="requirement_coverage",
        gap_kind="orphan_requirements",
        items=tuple(orphans),
        summary=summary,
    )


# ---------------------------------------------------------------------- #
# Check 2: milestone_realization (T-m8b stub)
# ---------------------------------------------------------------------- #


def compute_unrealized_milestone_requirements(
    project_root: Path, milestone_slug: str | None
) -> CoverageGap | None:
    """Within a single milestone's design run, find consumes
    requirements that no shipped feature realizes.

    Walks the chain:
      milestone.consumes_requirements
        → stories whose ``realizes_requirements`` includes the slug
        → features whose ``sources`` includes the story slug

    A requirement is **realized** when at least one feature exists
    whose sources list contains a story that realizes the
    requirement. Stories without features are NOT enough — M2's
    output is features; an unfeatured story means M2 has more work.

    Returns ``None`` when:
      - ``milestone_slug`` is None (no active scope; no check applies)
      - the milestone can't be found on disk
      - every consumed requirement is realized
    """
    if not milestone_slug:
        return None
    milestone_root = project_root / ".wonderland" / "milestones"
    if not milestone_root.is_dir():
        return None

    # Locate the active milestone's consumes list.
    milestone_consumes: list[str] = []
    for path in milestone_root.glob("milestone-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Match by Slug field rather than filename glob — operators
        # may hand-rename files but the Slug line is canonical.
        slug_line = re.search(
            r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
        )
        if slug_line and slug_line.group(1).strip() == milestone_slug:
            milestone_consumes = _parse_milestone_consumes(text)
            break

    if not milestone_consumes:
        return None

    # Filter out non-decomposable requirement kinds (persona /
    # situation / out_of_scope / deal_breaker) from the consumes
    # list before checking realization. Same exempt set as the
    # milestone-level check — a persona requirement is context for
    # every milestone's stories, not a buildable unit M2 has to
    # realize via a feature. Without this filter, Rabbit's
    # milestone-plan choices to consume a persona slug (which
    # happens when a milestone's named persona overlaps with a
    # persona-kind requirement) would force M2's coverage loop to
    # demand an impossible feature.
    req_root = project_root / ".wonderland" / "requirements"
    decomposable_consumes: list[str] = []
    if req_root.is_dir():
        # Read each requirement's kind by slug; treat missing as
        # decomposable so unknown shapes still surface to the operator.
        req_kinds: dict[str, str] = {}
        req_filename_re = re.compile(
            r"requirement-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
        )
        for path in req_root.glob("requirement-*.md"):
            m = req_filename_re.match(path.name)
            if not m:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            kind = _parse_requirement_kind(text)
            if kind is not None:
                req_kinds[m.group(1)] = kind
        for slug in milestone_consumes:
            kind = req_kinds.get(slug)
            if kind is not None and kind in _NON_REALIZABLE_REQUIREMENT_KINDS:
                continue
            decomposable_consumes.append(slug)
    else:
        decomposable_consumes = list(milestone_consumes)

    if not decomposable_consumes:
        return None

    # Build req → set[story_slug] map by reading every story's
    # realizes_requirements section + filename slug.
    story_root = project_root / ".wonderland" / "stories"
    req_to_stories: dict[str, set[str]] = {}
    story_filename_re = re.compile(
        r"story-(?:[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(.+)\.md"
    )
    if story_root.is_dir():
        for path in story_root.glob("story-*.md"):
            m = story_filename_re.match(path.name)
            if not m:
                continue
            story_slug = m.group(1)
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for req_slug in _parse_story_realizes(text):
                req_to_stories.setdefault(req_slug, set()).add(story_slug)

    # Build story → set[feature_slug] map by reading every feature's
    # Sources line. Story slugs that appear in features' sources are
    # the "realized" set at the story level.
    feature_root = project_root / ".wonderland" / "features"
    realized_stories: set[str] = set()
    if feature_root.is_dir():
        for path in feature_root.glob("feature-*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for src in _parse_feature_sources(text):
                realized_stories.add(src)

    # For each decomposable consumed requirement: realized iff at
    # least one story realizes it AND that story is sourced by a
    # feature. Non-decomposable kinds (persona / situation /
    # out_of_scope / deal_breaker) were filtered out above.
    unrealized: list[str] = []
    for req_slug in decomposable_consumes:
        stories = req_to_stories.get(req_slug, set())
        if not stories:
            unrealized.append(req_slug)
            continue
        if not any(s in realized_stories for s in stories):
            unrealized.append(req_slug)

    if not unrealized:
        return None

    summary = (
        f"Coverage gap: {len(unrealized)} requirement(s) in milestone "
        f"``{milestone_slug}`` are not realized by any feature — "
        f"{', '.join(unrealized[:5])}"
        + (f", + {len(unrealized) - 5} more" if len(unrealized) > 5 else "")
    )
    return CoverageGap(
        check_name="milestone_realization",
        gap_kind="unrealized_requirements",
        items=tuple(unrealized),
        summary=summary,
    )


# ---------------------------------------------------------------------- #
# Registry
# ---------------------------------------------------------------------- #


CheckFn = Callable[..., "CoverageGap | None"]


_MINIMUM_STORIES_THRESHOLD = 3


def compute_minimum_stories_gap(project_root: Path) -> CoverageGap | None:
    """Did M1 ship at least ``_MINIMUM_STORIES_THRESHOLD`` stories?

    Returns ``None`` when the floor is met (coverage complete);
    a ``CoverageGap`` with a count-based summary otherwise. The
    substrate's coverage-routing reads the summary as a nudge and
    extends rotation budget until either the floor's met or the
    extra-rotations cap exhausts.

    validation2 M1 deadlock motivation: three consecutive runs
    exited with 0 or 1 stories despite a foundation milestone
    needing 3-6. Constitutional + framing fixes were necessary but
    not sufficient; this is the substrate-side guarantee that M1
    rotation extends until the floor's met.
    """
    story_root = project_root / ".wonderland" / "stories"
    count = 0
    if story_root.is_dir():
        count = sum(
            1 for p in story_root.glob("story-*.md")
            if p.is_file()
        )
    if count >= _MINIMUM_STORIES_THRESHOLD:
        return None
    summary = (
        f"M1 coverage gap: {count} story/stories shipped; minimum "
        f"is {_MINIMUM_STORIES_THRESHOLD}. The agent named in the "
        f"M1 LEAD framing block (Caterpillar for foundation "
        f"milestones, Alice for capability) must ship "
        f"``decision: story`` with at least "
        f"{_MINIMUM_STORIES_THRESHOLD - count} more "
        f"stor{'y' if (_MINIMUM_STORIES_THRESHOLD - count) == 1 else 'ies'} "
        f"this rotation. Don't ask the operator clarifying "
        f"questions; the scope is in the milestone's "
        f"consumes_requirements + done_when."
    )
    return CoverageGap(
        check_name="minimum_stories",
        gap_kind="insufficient_stories",
        items=(),
        summary=summary,
    )


def compute_done_when_coverage_gap(
    project_root: Path, milestone_slug: str | None
) -> CoverageGap | None:
    """tdd-design-no-stories A/B variant check: every done-when
    bullet in the active milestone has at least one feature citing
    the milestone in its sources.

    Operates on a count-floor heuristic rather than item-level
    fingerprinting: features cite the milestone slug/guid (not
    individual done-when items), so the check verifies the
    feature-count for this milestone is at least the done-when
    count. A milestone with 4 done-when items and 1 feature shows
    as 3 items short.

    Returns ``None`` when:
      - ``milestone_slug`` is None (no active scope)
      - the milestone can't be found on disk
      - no done-when items parsed (degenerate milestone)
      - feature count >= done-when count
    """
    if not milestone_slug:
        return None
    milestone_root = project_root / ".wonderland" / "milestones"
    if not milestone_root.is_dir():
        return None

    done_when: list[str] = []
    milestone_guid: str | None = None
    for path in milestone_root.glob("milestone-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        slug_line = re.search(
            r"^\*\*Slug:\*\*\s*(\S+)", text, re.MULTILINE
        )
        if not (slug_line and slug_line.group(1).strip() == milestone_slug):
            continue
        done_when = _parse_milestone_done_when(text)
        guid_line = re.search(
            r"^\*\*GUID:\*\*\s*(\S+)", text, re.MULTILINE
        )
        if guid_line:
            milestone_guid = guid_line.group(1).strip()
        break

    if not done_when:
        return None

    # Count features citing this milestone in their sources.
    feature_root = project_root / ".wonderland" / "features"
    feature_count = 0
    if feature_root.is_dir():
        for path in feature_root.glob("feature-*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for src in _parse_feature_sources(text):
                # Accept slug-only, guid-only, or guid:slug.
                head = src.split(":", 1)[0]
                tail = src.split(":", 1)[1] if ":" in src else src
                if (
                    head == milestone_slug
                    or tail == milestone_slug
                    or (milestone_guid and head == milestone_guid)
                ):
                    feature_count += 1
                    break

    if feature_count >= len(done_when):
        return None

    gap = len(done_when) - feature_count
    summary = (
        f"Coverage gap: milestone ``{milestone_slug}`` has "
        f"{len(done_when)} done-when item(s) but only "
        f"{feature_count} feature(s) cite it. Rabbit must ship "
        f"at least {gap} more feature(s) sourcing the milestone "
        f"to cover the remaining done-when items. Cite the "
        f"milestone slug ``{milestone_slug}`` (or its GUID) in "
        f"each new feature's Sources line."
    )
    return CoverageGap(
        check_name="done_when_coverage",
        gap_kind="underpowered_done_when",
        items=tuple(done_when[feature_count:]),
        summary=summary,
    )


_CHECK_REGISTRY: dict[str, CheckFn] = {
    "requirement_coverage": compute_orphan_requirements,
    "milestone_realization": compute_unrealized_milestone_requirements,
    "minimum_stories": compute_minimum_stories_gap,
    "done_when_coverage": compute_done_when_coverage_gap,
}


def run_coverage_check(
    check_name: str,
    project_root: Path,
    *,
    milestone_slug: str | None = None,
) -> CoverageGap | None:
    """Dispatch into the registered check. Returns the gap (or None
    when coverage is complete / check is unknown / project_root is
    missing). Silent on registry miss so a typo in the phase YAML
    doesn't crash the meeting — operator notices via the absent
    nudges and corrects the YAML."""
    if project_root is None:
        return None
    fn = _CHECK_REGISTRY.get(check_name)
    if fn is None:
        return None
    try:
        if check_name in ("milestone_realization", "done_when_coverage"):
            return fn(project_root, milestone_slug)
        return fn(project_root)
    except Exception:  # noqa: BLE001 — coverage is informational
        return None


def register_check(name: str, fn: CheckFn) -> None:
    """Plug a new check into the registry. Used by tests + by future
    extensions; the bundled checks register themselves at import."""
    _CHECK_REGISTRY[name] = fn


def list_checks() -> list[str]:
    """Names of every registered check. Useful for CLI / docs."""
    return sorted(_CHECK_REGISTRY.keys())
