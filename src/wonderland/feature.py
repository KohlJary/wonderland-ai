"""Feature writer + registry — Rabbit's grouping artifact for M2.5.

Per the M2/M3 gap surfaced in analysis 026/027 and roadmap d1f4f2ec:
M3 contract-negotiation seeds from a single ticket and Tweedles
generalize from there, which produces the inconsistent-frontend-vs-
backend pattern observed across runs. Features are tickets *grouped*
into user-facing units that span the stack coherently, so M3 can
negotiate seams against a feature instead of one ticket at a time.

Storage: ``<project_root>/.wonderland/features/feature-NNN-slug.md``,
3-digit zero-padded numbering. Same single-source-of-truth approach
as TicketRegistry — no separate counter file; ``next_number()``
derives from scanning existing features.

Validation is deliberately looser than tickets. Tickets pin scope,
estimate, and dependencies because the Rabbit's discipline says they
must; features are organizational — title, description, and at least
one constituent ticket are required, the rest is free-form. The
discipline lives at the ticket layer; features carry the user-facing
framing on top.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from wonderland.adr import slugify
from wonderland.ticket import TicketTier

from wonderland.artifact_guid import new_artifact_guid, short_guid

FEATURES_DIRNAME = "features"
# T-g3: filename's id-part is either an 8-char ULID prefix (new) or
# a 1-4 digit legacy number (pre-P18).
_FILENAME_PATTERN = re.compile(
    r"^feature-(?P<id>[0-9A-HJKMNP-TV-Z]{8}|\d{1,4})-(?P<slug>[a-z0-9-]+)\.md$"
)
_GUID_PATTERN = re.compile(r"^\*\*GUID:\*\*\s*([0-9A-HJKMNP-TV-Z]{26})\s*$", re.MULTILINE)
_NUMBER_FROM_H2 = re.compile(r"^##\s*Feature\s+(\d+)\s*:", re.MULTILINE)


class StackSpan(StrEnum):
    """Which side of the stack a feature touches.

    Knowing this up front lets M3's contract negotiation pre-flight
    the right seams: full-stack features need both Tweedles aligned
    on the contract; backend-only or frontend-only features can be
    handled on one side. The pattern Tweedles missed in prior runs
    was full-stack work that they negotiated as if it were one-sided.
    """

    FRONTEND = "frontend"
    BACKEND = "backend"
    FULL_STACK = "full-stack"


class FeatureKind(StrEnum):
    """Whether the feature is a user-facing capability or foundational
    plumbing.

    Capabilities are user-meaningful — Alice's persona-driven stories
    compose into them. Foundations are developer-meaningful —
    Caterpillar's plumbing stories (mock data, observability,
    environment config, build tooling) compose into them. Same
    lifecycle, same decomposition into tickets, same dashboard view —
    the discriminator just tells agents what kind of work this is so
    M2 doesn't get hung up on "is mock-data setup really a feature?"
    semantic debates.

    Default is CAPABILITY for back-compat: features shipped before
    this field existed are user-facing capabilities by definition,
    and the default keeps existing payloads valid without a kind:
    field.
    """

    CAPABILITY = "capability"
    FOUNDATION = "foundation"


class FeaturePayload(BaseModel):
    """Structured payload Rabbit attaches to a feature-issuing utterance."""

    guid: str = Field(default_factory=new_artifact_guid)
    """P18 — stable artifact identity. ULID generated at creation,
    preserved across re-emissions. Rabbit re-emits with the same
    guid to amend an existing feature; coining a new guid creates
    a new feature. Substrate routes on guid; slug is cosmetic.
    Validation4 pilot's 9-features-for-3-concepts was exactly the
    case this primitive eliminates."""

    title: str = Field(min_length=1)
    description: str = Field(
        min_length=1,
        description="What user-facing thing this feature delivers, in plain language.",
    )
    kind: FeatureKind = Field(
        default=FeatureKind.CAPABILITY,
        description=(
            "capability (default) for user-facing features; "
            "foundation for plumbing/developer-experience work like "
            "mock data, observability, env config, build tooling. "
            "Functionally identical lifecycle; the kind drives "
            "context-appropriate framing so M2 doesn't argue "
            "semantics for stories whose persona is a developer."
        ),
    )
    tickets: list[str] = Field(
        default_factory=list,
        description=(
            "Slugs of constituent tickets this feature aggregates. "
            "Informational only — the source-of-truth for "
            "ticket→feature membership is each ticket's "
            "``Sources:`` field, written by M3 (Rabbit's "
            "decomposition meeting). When M2 ships a feature, "
            "this list is typically empty; M3 populates it later "
            "when tickets get decomposed (via the reverse-index "
            "in ``_ticket_to_feature_map``). Pre-T88 workflows "
            "where tickets came before features used this as the "
            "primary link, hence the field stays for back-compat "
            "even though it's no longer load-bearing."
        ),
    )
    personas: list[str] = Field(
        default_factory=list,
        description="Persona names from M1 stories that this feature serves.",
    )
    stack_span: StackSpan
    tier: TicketTier
    sources: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Story slugs whose intent this feature realizes. "
            "REQUIRED and non-empty — a feature without source "
            "stories is an unmoored claim; M3 decomposition needs "
            "the story chain to know what the feature was supposed "
            "to deliver and the T-m8b coverage check walks "
            "milestone.consumes_requirements → stories realizing "
            "those → features sourcing those stories. An empty "
            "sources list breaks that walk + leaves the feature "
            "orphaned in lifecycle queries."
        ),
    )
    milestone: str | None = Field(
        default=None,
        description=(
            "T-ab5 — explicit milestone attribution. Slug or "
            "``<guid>:<slug>`` of the milestone this feature "
            "belongs to. When the design run was launched with "
            "``--milestone <slug>``, Rabbit populates this with "
            "the active milestone's slug — no inference required. "
            "Substrate attribution (seed-loader scope filter, TUI "
            "per-feature grouping) reads this field directly when "
            "present; Jaccard-based attribution is the back-compat "
            "fallback for features shipped before this field "
            "existed. A feature belongs to exactly one milestone; "
            "if a feature's scope spans, split it into two "
            "features rather than naming two milestones."
        ),
    )


@dataclass(frozen=True)
class FeatureRecord:
    number: int
    guid: str
    slug: str
    title: str
    path: Path
    kind: FeatureKind = FeatureKind.CAPABILITY
    """T-ab69: was missing from FeatureRecord, causing the autopromoted
    kind in FeatureRegistry.write to never reach callers (notably
    white_rabbit._record_features which builds the bus artifact). The
    bus artifact's kind drives downstream M3 per_item_roster_filter —
    so a stale 'capability' here routed foundation milestones through
    Alice's capability flow. Filled at write() time from the validated
    (possibly-autopromoted) payload."""
    milestone: str | None = None
    """T-ab73: ticket-scope validation needs to read a feature's
    milestone via the parent registry lookup. Same shape as ``kind``
    above — was missing, so TicketRegistry.write couldn't decide
    whether a sourced feature belongs to the active milestone.
    Filled at write() time from the validated payload and parsed
    from disk on ``_record_from_path``."""

    def read(self) -> str:
        return self.path.read_text(encoding="utf-8")


def render_feature(number: int, payload: FeaturePayload) -> str:
    """Render a feature payload as the markdown that lands on disk."""
    lines: list[str] = [
        f"## Feature {number:03d}: {payload.title}",
        "",
        f"**GUID:** {payload.guid}",
        f"**Kind:** {payload.kind.value}",
        f"**Milestone:** {payload.milestone or '—'}",
        f"**Sources:** {_join_or_dash(payload.sources)}",
        f"**Personas:** {_join_or_dash(payload.personas)}",
        f"**Stack span:** {payload.stack_span.value}",
        f"**Tier:** {payload.tier.value}",
        "",
        "**Description:**",
        "",
        payload.description.rstrip(),
        "",
        "**Constituent tickets:**",
    ]
    if payload.tickets:
        lines.extend(f"- {ticket}" for ticket in payload.tickets)
    else:
        # Empty tickets is normal at M2 ship time — M3 hasn't run
        # yet. Surface a "to be decomposed" placeholder so the file
        # is human-readable instead of "this should not happen,"
        # which used to be true under the pre-T88 workflow but
        # isn't anymore.
        lines.append("- *(to be decomposed in M3)*")
    lines.append("")
    return "\n".join(lines)


def _join_or_dash(items: list[str]) -> str:
    return ", ".join(items) if items else "—"


class FeatureRegistry:
    """Read/write registry over ``<project_root>/.wonderland/features/``.

    Same shape as TicketRegistry: numbering derives from scanning
    existing files; no separate counter to keep in sync.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root / ".wonderland" / FEATURES_DIRNAME

    @property
    def path(self) -> Path:
        return self._root

    def list_features(self) -> list[FeatureRecord]:
        if not self._root.is_dir():
            return []
        records: list[FeatureRecord] = []
        for entry in self._root.iterdir():
            if not entry.is_file():
                continue
            record = self._record_from_path(entry)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.number)
        return records

    def next_number(self) -> int:
        existing = self.list_features()
        if not existing:
            return 1
        return max(r.number for r in existing) + 1

    def find_by_slug(self, slug: str) -> FeatureRecord | None:
        for record in self.list_features():
            if record.slug == slug:
                return record
        return None

    def find_by_guid(self, guid: str) -> FeatureRecord | None:
        """P18 T-g2 — primary identity lookup. Returns None for
        empty/unknown guid so callers fall through to slug-based
        back-compat."""
        if not guid:
            return None
        for record in self.list_features():
            if record.guid == guid:
                return record
        return None

    def find_by_number(self, number: int) -> FeatureRecord | None:
        for record in self.list_features():
            if record.number == number:
                return record
        return None

    def write(self, payload: FeaturePayload | dict) -> FeatureRecord:
        """Create or update a feature by slug — update-by-slug
        semantics mirror MilestoneRegistry. Re-emit with the same
        slug overwrites in place (preserves number); new slug
        appends with the next available number. P15 follow-up
        aligning the design-time registries with the planning
        registry's dedup shape."""
        validated = (
            payload
            if isinstance(payload, FeaturePayload)
            else FeaturePayload.model_validate(payload)
        )

        # T-ab67 — feature.kind inherits milestone.kind for foundation
        # milestones. v3/v4/v5/v6 LDR-rerun all shipped features tagged
        # ``kind: capability`` under M1 milestones tagged
        # ``kind: foundation``. The default FeaturePayload.kind is
        # CAPABILITY (back-compat); agents emit features without thinking
        # hard about the kind field. The result: T-ab50/T-ab65's
        # milestone-layer foundation routing didn't propagate to the
        # feature layer, so feature-shape framing in M3 decomposition
        # stayed capability-shape (user-flow tickets) even under
        # foundation milestones (which should produce infra tickets).
        #
        # Autopromote pattern, same shape as T-ab65: if the active
        # milestone is foundation, ratify that signal at the feature
        # layer too. Capability milestones are unaffected — features
        # within them stay whatever the agent emitted.
        try:
            from wonderland.workflow import get_active_milestone_scope
            _ab67_scope = get_active_milestone_scope()
        except Exception:  # noqa: BLE001 — best-effort
            _ab67_scope = None
        # T-ab69 diagnostic: log every feature.write's scope view so
        # we can correlate against expected autopromote firings. v10
        # had 3 features composed capability under foundation milestone
        # with ZERO autopromote events — need to know whether scope
        # was None, scope.kind was wrong, or some other path.
        import sys
        _ab69_scope_repr = (
            f"slug={_ab67_scope.slug!r} kind={getattr(_ab67_scope, 'kind', None)!r}"
            if _ab67_scope is not None
            else "None"
        )
        sys.stderr.write(
            f"[feature-write-debug] title={validated.title!r} "
            f"feature.kind={validated.kind.value} "
            f"feature.milestone={validated.milestone!r} "
            f"scope={_ab69_scope_repr}\n"
        )
        if (
            _ab67_scope is not None
            and getattr(_ab67_scope, "kind", None) == "foundation"
            and validated.kind != FeatureKind.FOUNDATION
        ):
            sys.stderr.write(
                f"[feature-autopromote] title={validated.title!r} "
                f"kind: {validated.kind.value} → foundation "
                f"(parent milestone {_ab67_scope.slug!r} is foundation)\n"
            )
            validated = validated.model_copy(
                update={"kind": FeatureKind.FOUNDATION}
            )

        # T-ab18 — reject cross-milestone feature emissions during
        # milestone-scoped runs. When the run is scoped to milestone
        # X and the feature's milestone field names a different
        # milestone, the agent is cross-emitting (proposing work
        # outside the active scope). Such features get correctly
        # filtered out of T-ab17's iteration, but the emission
        # itself burns budget and produces dead artifacts on disk.
        # Reject at write time so the agent gets the error back
        # and either re-emits with the active milestone slug OR
        # surfaces the cross-scope concern as a ``concern`` /
        # ``question_to_operator``, which is the substrate-correct
        # channel for "I see work that belongs elsewhere."
        #
        # Permissive when:
        #   - no active milestone scope (workflow isn't milestone-
        #     scoped; e.g. ad-hoc design runs)
        #   - feature.milestone is None (legacy / pre-T-ab5
        #     emission; can't enforce a contract that wasn't
        #     declared)
        #
        # Observed: mvp-demo-rerun-A M3 design produced 6 features
        # all tagged ``milestone: m2-editor-ui-and-search`` —
        # cross-emission. T-ab17 filtered them out of iteration but
        # M4 architecture still burned budget producing an empty
        # ADR on the 0-ticket result. The reject-at-write path
        # would have surfaced the error to Rabbit on his first
        # emission, allowing him to retry with the active milestone
        # or escalate as a concern.
        try:
            from wonderland.workflow import get_active_milestone_scope
            active_scope = get_active_milestone_scope()
        except Exception:  # noqa: BLE001 — best-effort
            active_scope = None
        if active_scope is not None and validated.milestone:
            cited_slug = (
                validated.milestone.split(":", 1)[1]
                if ":" in validated.milestone
                else validated.milestone
            )
            if cited_slug != active_scope.slug:
                raise ValueError(
                    f"feature {validated.title!r}: ``milestone`` "
                    f"field is set to {cited_slug!r} but the "
                    f"active run scope is {active_scope.slug!r}. "
                    f"Features emitted during a milestone-scoped "
                    f"design run must belong to the active "
                    f"milestone. If you see work that belongs to "
                    f"another milestone, surface it as a "
                    f"``concern`` (or ``question_to_operator`` "
                    f"for a load-bearing scope question) — those "
                    f"are the substrate-correct channels for "
                    f"cross-scope observations. Re-emit this "
                    f"feature with ``milestone: {active_scope.slug}`` "
                    f"if it actually belongs to the active "
                    f"milestone, OR retract and replace with a "
                    f"concern."
                )

        # T-ab76: auto-stamp the active milestone when the agent left
        # the field None during a milestone-scoped run. The substrate
        # KNOWS the scope — relying on the agent to repeat it left
        # feature.milestone None on most real runs (ldr-final M1: the
        # composed feature carried no milestone), which silently
        # no-ops BOTH T-ab73 (ticket scope-lock) and T-ab74 (content-
        # leak gate) because both resolve ticket -> parent feature ->
        # milestone. Stamping here makes the field reliable so those
        # gates actually fire. Only when scoped + None; an explicit
        # mismatching milestone already raised above.
        if active_scope is not None and not validated.milestone:
            validated = validated.model_copy(
                update={"milestone": active_scope.slug}
            )

        slug = slugify(validated.title)
        # T-g2: guid-first lookup; slug fallback for back-compat.
        existing = self.find_by_guid(validated.guid)
        if existing is None:
            existing = self.find_by_slug(slug)

        if existing is not None:
            number = existing.number
            full_path = existing.path
        else:
            number = self.next_number()
            # T-g3: filename embeds short_guid for substrate identity.
            filename = f"feature-{short_guid(validated.guid)}-{slug}.md"
            full_path = self._root / filename

        # Preserve existing artifact's guid on slug-fallback match.
        if existing is not None and existing.guid:
            validated = validated.model_copy(update={"guid": existing.guid})

        self._root.mkdir(parents=True, exist_ok=True)
        full_path.write_text(render_feature(number, validated), encoding="utf-8")

        return FeatureRecord(
            number=number,
            guid=validated.guid,
            slug=slug,
            title=validated.title,
            path=full_path,
            kind=validated.kind,
            milestone=validated.milestone,
        )

    @staticmethod
    def _record_from_path(path: Path) -> FeatureRecord | None:
        match = _FILENAME_PATTERN.match(path.name)
        if not match:
            return None
        id_part = match.group("id")
        slug = match.group("slug")
        title = FeatureRegistry._title_from_file(path, fallback=slug)
        guid = FeatureRegistry._guid_from_file(path)
        number = FeatureRegistry._number_from_file(path, id_part)
        # T-ab69: parse Kind so callers reading existing features see
        # the persisted kind, not the default. Mirrors the milestone
        # parser shape; back-compat falls through to CAPABILITY for
        # files predating the kind field.
        kind = FeatureRegistry._kind_from_file(path)
        # T-ab73: parse Milestone so TicketRegistry.write can resolve
        # the parent feature's milestone for cross-milestone scope-lock.
        # Same pattern as kind — back-compat falls through to None.
        milestone = FeatureRegistry._milestone_from_file(path)
        return FeatureRecord(
            number=number, guid=guid, slug=slug, title=title, path=path,
            kind=kind, milestone=milestone,
        )

    @staticmethod
    def _milestone_from_file(path: Path) -> str | None:
        """T-ab73: parse the ``**Milestone:**`` line from a feature file.
        Default None for back-compat with pre-T-ab5 files. Strips the
        em-dash placeholder that render_feature uses when the payload
        had no milestone field set."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return None
        m = re.search(r"^\*\*Milestone:\*\*\s*(.+)$", text, re.MULTILINE)
        if not m:
            return None
        value = m.group(1).strip()
        if not value or value == "—":
            return None
        return value

    @staticmethod
    def _kind_from_file(path: Path) -> FeatureKind:
        """T-ab69: parse the ``**Kind:**`` line from a feature file.
        Default CAPABILITY for back-compat with pre-kind files."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return FeatureKind.CAPABILITY
        m = re.search(r"^\*\*Kind:\*\*\s*(\S+)", text, re.MULTILINE)
        if not m:
            return FeatureKind.CAPABILITY
        try:
            return FeatureKind(m.group(1).strip().lower())
        except ValueError:
            return FeatureKind.CAPABILITY

    @staticmethod
    def _number_from_file(path: Path, id_part: str) -> int:
        """T-g3 — legacy filenames carried number in the id slot;
        new-shape files keep it only in the H2 header."""
        if id_part.isdigit():
            return int(id_part)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return 0
        m = _NUMBER_FROM_H2.search(text)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _guid_from_file(path: Path) -> str:
        """Extract the ``**GUID:**`` line; fresh ULID if pre-P18 file."""
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return new_artifact_guid()
        m = _GUID_PATTERN.search(text)
        return m.group(1) if m else new_artifact_guid()

    @staticmethod
    def _title_from_file(path: Path, *, fallback: str) -> str:
        try:
            with path.open(encoding="utf-8") as f:
                first_line = f.readline().strip()
        except OSError:
            return fallback
        if not first_line.startswith("## Feature") or ":" not in first_line:
            return fallback
        return first_line.split(":", 1)[1].strip() or fallback


__all__ = [
    "FEATURES_DIRNAME",
    "FeaturePayload",
    "FeatureRecord",
    "FeatureRegistry",
    "StackSpan",
    "render_feature",
]
