"""Tests for cross-run seed continuity via disk-backed artifact
fallback (analysis 039 redux fix)."""

from __future__ import annotations

from pathlib import Path

import pytest

from wonderland.seeds_fallback import (
    disk_seeds_for_kinds,
    supported_disk_kinds,
)
from wonderland.utterance import SpeechAct


def _seed_placeholder_stories(tmp_path: Path, slugs: list[str]) -> None:
    """Register stories whose slug matches each entry in ``slugs`` so
    downstream ticket/feature fixtures can cite them without tripping
    the phantom-citation filter in ``_load_features`` / ``_load_tickets``.

    Pre-filter, tests citing fictional slugs (``"s"``, ``"x"``,
    ``"see-my-money-at-a-glance"``) silently produced corrupted records
    that downstream meetings inherited; the filter rightly drops those
    now, so tests that exercise seed-loading-SHAPE (not
    citation-correctness) need to register the placeholder story first.
    """
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.adr import slugify

    registry = StoryRegistry(tmp_path)
    for slug in slugs:
        # Slugify the slug back into a title the story renderer accepts.
        title = slug.replace("-", " ").capitalize() or "placeholder"
        registry.write(StoryPayload(
            title=title,
            persona="placeholder persona",
            situation="placeholder",
            need=f"As placeholder I want {title} so tests pass.",
            acceptance=["placeholder acceptance"],
            tier="core",
            confusion_flags=["placeholder confusion"],
        ))
        # Re-slugified title may not equal the requested slug if the
        # input slug contained chars slugify normalizes; the helper
        # assumes the caller passed already-slugified strings (the
        # case for all existing fixtures).
        assert slugify(title) == slug, (
            f"placeholder story slug mismatch: requested {slug!r}, "
            f"got {slugify(title)!r}"
        )


# --- Empty-state behavior ---


def test_disk_seeds_empty_when_project_has_no_wonderland_dir(
    tmp_path: Path,
) -> None:
    """Project that's never been run on returns no seeds."""
    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket", "story"], thread_id="composition"
    )
    assert seeds == []


def test_disk_seeds_empty_for_unsupported_kind(tmp_path: Path) -> None:
    """A kind we don't have a loader for is silently skipped."""
    seeds = disk_seeds_for_kinds(
        tmp_path, ["nonexistent-kind"], thread_id="x"
    )
    assert seeds == []


def test_disk_seeds_empty_when_registry_dir_exists_but_empty(
    tmp_path: Path,
) -> None:
    """Empty registry directories are not an error."""
    (tmp_path / ".wonderland" / "tickets").mkdir(parents=True)
    seeds = disk_seeds_for_kinds(tmp_path, ["ticket"], thread_id="x")
    assert seeds == []


# --- Loaded-state behavior ---


def test_disk_seeds_loads_tickets_from_disk(tmp_path: Path) -> None:
    """When tickets exist on disk, they surface as synthetic
    utterances with the right speech_act + speaker."""
    from wonderland.ticket import TicketPayload, TicketRegistry

    _seed_placeholder_stories(tmp_path, ["see-my-money-at-a-glance"])

    registry = TicketRegistry(tmp_path)
    registry.write(TicketPayload(
        title="Build account aggregation API",
        owner="tweedledum",
        tier="v1",
        estimate="2 days",
        description="Aggregate account balances for Maya's dashboard.",
        sources=["see-my-money-at-a-glance"],
    ))
    registry.write(TicketPayload(
        title="Build transaction list UI",
        owner="tweedledee",
        tier="v1",
        estimate="1 day",
        description="List recent transactions in a TUI table.",
        sources=["see-my-money-at-a-glance"],
    ))

    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket"], thread_id="decomposition"
    )
    assert len(seeds) == 2
    # Speaker matches the agent who normally produces tickets.
    for seed in seeds:
        assert seed.speaker.name == "white_rabbit"
        assert seed.speech_act == SpeechAct.TICKET
        assert seed.is_seed is True
        assert seed.thread_id == "decomposition"
        assert len(seed.content.artifacts) == 1
        assert seed.content.artifacts[0].kind == "ticket"
    # Records came through with title.
    titles = {s.content.artifacts[0].payload["title"] for s in seeds}
    assert "Build account aggregation API" in titles
    assert "Build transaction list UI" in titles


def test_disk_seeds_loads_stories(tmp_path: Path) -> None:
    """Stories synthesize with alice as speaker."""
    from wonderland.story import StoryPayload, StoryRegistry

    StoryRegistry(tmp_path).write(StoryPayload(
        title="See my money at a glance",
        persona="Maya, freelance translator",
        situation="Sunday evening, five tabs open.",
        need="Glance and know.",
        acceptance=["Single view", "All accounts visible"],
        tier="core",
        confusion_flags=["What counts as 'recent' for transactions?"],
    ))
    seeds = disk_seeds_for_kinds(tmp_path, ["story"], thread_id="scoping")
    assert len(seeds) == 1
    assert seeds[0].speaker.name == "alice"
    assert seeds[0].speech_act == SpeechAct.STORY


def test_disk_seeds_multiple_kinds_in_one_call(tmp_path: Path) -> None:
    """A single call with multiple kinds returns synthesized utterances
    for each kind that has files."""
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.story import StoryPayload, StoryRegistry

    _seed_placeholder_stories(tmp_path, ["x"])

    TicketRegistry(tmp_path).write(TicketPayload(
        title="T",
        owner="tweedledum",
        tier="v1",
        estimate="1 day",
        description="d",
        sources=["x"],
    ))
    StoryRegistry(tmp_path).write(StoryPayload(
        title="S",
        persona="P",
        situation="x",
        need="y",
        acceptance=["a"],
        tier="core",
        confusion_flags=["unsure"],
    ))

    seeds = disk_seeds_for_kinds(
        tmp_path, ["ticket", "story"], thread_id="composition"
    )
    # 1 ticket + 1 explicit story + 1 placeholder story (from the
    # citation-filter setup helper) = 3 seeds. The test's intent is
    # "multiple kinds surface in one call"; that holds regardless of
    # exact story count.
    assert len(seeds) == 3
    kinds = {s.content.artifacts[0].kind for s in seeds}
    assert kinds == {"ticket", "story"}


def test_disk_seeds_artifact_payload_has_slug_for_per_item_slicing(
    tmp_path: Path,
) -> None:
    """The synthesized artifact's payload carries `slug` so the
    resolve_seeds per-item slicing logic can route the right feature
    to the right iteration."""
    from wonderland.feature import FeaturePayload, FeatureRegistry

    _seed_placeholder_stories(tmp_path, ["see-my-money-at-a-glance"])

    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Balance dashboard",
        description="Show account balances at a glance.",
        tickets=["build-balance-card-ui"],
        stack_span="full-stack",
        tier="v1",
        sources=["see-my-money-at-a-glance"],
    ))
    seeds = disk_seeds_for_kinds(
        tmp_path, ["feature"], thread_id="composition"
    )
    assert len(seeds) == 1
    payload = seeds[0].content.artifacts[0].payload
    assert payload["slug"] == "balance-dashboard"
    assert payload["number"] == 1
    assert payload["title"] == "Balance dashboard"
    assert "path" in payload


# --- supported_disk_kinds ---


def test_supported_disk_kinds_includes_load_bearing_artifacts() -> None:
    """The kinds that matter most for cross-run continuity are wired."""
    kinds = supported_disk_kinds()
    assert "ticket" in kinds
    assert "story" in kinds
    assert "feature" in kinds
    assert "adr" in kinds
    assert "contract_note" in kinds
    # The operator's directive — gives architectural meetings (Cat's
    # M4) a way to read the launching prompt verbatim.
    assert "directive" in kinds


# --- Directive seed (operator's literal launching prompt) ---


def test_disk_seeds_loads_directive_body_not_yaml_envelope(
    tmp_path: Path,
) -> None:
    """The synthetic utterance body should be the directive's
    ``body`` field (the operator's literal prompt), not the YAML
    envelope. Otherwise Cat reads ``name: obol\\ntitle: obol\\n...``
    and has to mentally parse to find the actual prompt."""
    from wonderland.directive import DirectivePreset, save_directive

    save_directive(
        DirectivePreset(
            name="my-app",
            title="My App",
            body="Build a TUI dashboard for personal finance.",
        ),
        tmp_path,
    )
    seeds = disk_seeds_for_kinds(
        tmp_path, ["directive"], thread_id="architecture"
    )
    assert len(seeds) == 1
    body = seeds[0].content.body
    # The directive's prompt is the body, verbatim. (save_directive
    # appends a trailing newline as part of its serialization
    # convention; we rstrip here to compare against the source text.)
    assert body.rstrip() == "Build a TUI dashboard for personal finance."
    # Crucial: the YAML envelope (name:/title:/body:) does NOT leak
    # into the body — Cat reads the prompt as-if a teammate said it.
    assert "name:" not in body
    assert "title:" not in body


def test_disk_seeds_directive_attributed_to_dodo(tmp_path: Path) -> None:
    """The directive flows in via the Dodo at runtime via
    relay_directive(). The disk-fallback synthetic utterance keeps
    the same speaker identity so post-hoc analysis can't tell the
    two paths apart."""
    from wonderland.directive import DirectivePreset, save_directive

    save_directive(
        DirectivePreset(name="x", title="x", body="do the thing"),
        tmp_path,
    )
    seeds = disk_seeds_for_kinds(tmp_path, ["directive"], thread_id="t")
    assert seeds[0].speaker.name == "dodo"
    assert seeds[0].speech_act == SpeechAct.DIRECTIVE


def test_disk_seeds_directive_carries_artifact_for_per_item_slicing(
    tmp_path: Path,
) -> None:
    """Each directive seed carries one ``directive`` artifact whose
    payload has the standard slug/title/path shape — so per_item
    iteration code that filters by artifact kind treats directives
    consistently with stories/tickets/features."""
    from wonderland.directive import DirectivePreset, save_directive

    save_directive(
        DirectivePreset(name="my-app", title="My App", body="x"),
        tmp_path,
    )
    seeds = disk_seeds_for_kinds(tmp_path, ["directive"], thread_id="t")
    artifact = seeds[0].content.artifacts[0]
    assert artifact.kind == "directive"
    assert artifact.payload["slug"] == "my-app"
    assert artifact.payload["title"] == "My App"


# --- Integration with resolve_seeds ---


class TestResolveSeedsDiskFallback:
    """resolve_seeds wires disk fallback when project_root is set
    AND the bus query for a binding produces no results. Bus content
    always wins when present."""

    def _empty_capture(self):
        from wonderland.workflow import WorkflowCapture

        return WorkflowCapture()

    def test_bus_results_skip_disk_fallback(self, tmp_path: Path) -> None:
        """If the bus has matching utterances, disk content does NOT
        get added (bus is authoritative)."""
        from wonderland.story import StoryPayload, StoryRegistry
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.utterance import (
            AgentIdentity,
            Artifact,
            Utterance,
            UtteranceContent,
        )
        from wonderland.workflow import (
            SeedBinding,
            WorkflowCapture,
            resolve_seeds,
        )

        # Disk has a ticket
        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        # Bus has a different ticket on the decomposition thread
        capture = WorkflowCapture()
        capture.observe(Utterance(
            thread_id="decomposition",
            speaker=AgentIdentity(name="white_rabbit", constitution_version="0.1"),
            addressed_to="caucus",
            speech_act=SpeechAct.TICKET,
            content=UtteranceContent(
                body="bus body",
                artifacts=[Artifact(kind="ticket", payload={
                    "title": "T-from-bus",
                    "slug": "t-from-bus",
                    "number": 1,
                })],
            ),
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        seeds = resolve_seeds(
            [binding], capture, project_root=tmp_path
        )
        # Only the bus version is present; disk is skipped because
        # bus had results.
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["title"] == "T-from-bus"

    def test_empty_bus_falls_back_to_disk(self, tmp_path: Path) -> None:
        """When the bus is empty for a binding, disk artifacts surface
        as synthetic seed utterances."""
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        _seed_placeholder_stories(tmp_path, ["s"])

        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        seeds = resolve_seeds(
            [binding], self._empty_capture(), project_root=tmp_path
        )
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["title"] == "T-from-disk"

    def test_no_project_root_no_fallback(self, tmp_path: Path) -> None:
        """resolve_seeds called WITHOUT project_root retains the prior
        behavior: empty bus → empty seeds. Back-compat for any caller
        that hasn't wired the new param yet."""
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        TicketRegistry(tmp_path).write(TicketPayload(
            title="T-from-disk",
            owner="tweedledum",
            tier="v1",
            estimate="1 day",
            description="x",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"]}
        )
        # No project_root passed
        seeds = resolve_seeds([binding], self._empty_capture())
        assert seeds == []

    def test_disk_fallback_respects_limit(self, tmp_path: Path) -> None:
        from wonderland.ticket import TicketPayload, TicketRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        _seed_placeholder_stories(tmp_path, ["s"])

        for i in range(5):
            TicketRegistry(tmp_path).write(TicketPayload(
                title=f"T-{i}",
                owner="tweedledum",
                tier="v1",
                estimate="1 day",
                description="x",
                sources=["s"],
            ))

        binding = SeedBinding.model_validate(
            {"from": "decomposition", "kinds": ["ticket"], "limit": 2}
        )
        seeds = resolve_seeds(
            [binding], self._empty_capture(), project_root=tmp_path
        )
        assert len(seeds) == 2

    def test_disk_fallback_per_item_slicing_works(
        self, tmp_path: Path
    ) -> None:
        """When inside a per_item iteration, disk-loaded artifacts
        for the iteration kind get sliced to the current item's slug.
        Same logic applies to disk content as bus content because
        both end up in the `kinded` list before the slice runs."""
        from wonderland.feature import FeaturePayload, FeatureRegistry
        from wonderland.workflow import (
            SeedBinding,
            resolve_seeds,
        )

        _seed_placeholder_stories(tmp_path, ["s"])

        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature One",
            description="d",
            tickets=["t1"],
            stack_span="full-stack",
            tier="v1",
            sources=["s"],
        ))
        FeatureRegistry(tmp_path).write(FeaturePayload(
            title="Feature Two",
            description="d",
            tickets=["t2"],
            stack_span="full-stack",
            tier="v1",
            sources=["s"],
        ))

        binding = SeedBinding.model_validate(
            {"from": "composition", "kinds": ["feature"]}
        )
        seeds = resolve_seeds(
            [binding],
            self._empty_capture(),
            project_root=tmp_path,
            current_item_kind="feature",
            current_item_slug="feature-one",
        )
        # Only the feature-one slice should be present.
        assert len(seeds) == 1
        assert seeds[0].content.artifacts[0].payload["slug"] == "feature-one"


# ====================================================================
# Phantom-citation drift filter — substrate bugs 0c98c694 + 9231bcd5
# from the obol M3 pilot. On-emission strip catches phantom slugs at
# composition time; this filter catches drift that happens AFTER
# emission (cited story retracted, cited file lost, etc.). Without
# it, broken-citation artifacts leaked into every downstream
# milestone's seed pool — observed as the M3 caucus loop on
# Feature 002.
# ====================================================================


def test_collect_phantom_citations_clean_feature(tmp_path: Path) -> None:
    """A feature citing only real stories on disk returns no phantoms."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.workflow import collect_phantom_citations

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Kohl logs a transaction",
        persona="Kohl",
        situation="end of week",
        need="As Kohl I want to log so I can track.",
        acceptance=["a"], tier="core",
        confusion_flags=["c"],
    ))
    phantoms = collect_phantom_citations(
        ["kohl-logs-a-transaction"],
        tmp_path,
        citing_kind="feature",
    )
    assert phantoms == []


def test_collect_phantom_citations_surfaces_unresolved_slug(
    tmp_path: Path,
) -> None:
    """The bug shape: a slug that names no story on disk shows up
    as a phantom."""
    from wonderland.workflow import collect_phantom_citations

    # No stories registered.
    phantoms = collect_phantom_citations(
        ["kohl-does-something-that-does-not-exist"],
        tmp_path,
        citing_kind="feature",
    )
    assert phantoms == ["kohl-does-something-that-does-not-exist"]


def test_collect_phantom_citations_mixed_keeps_real_drops_phantom(
    tmp_path: Path,
) -> None:
    """Feature 002's exact shape: some sources resolve, some don't.
    The phantoms list contains only the unresolved entries."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.workflow import collect_phantom_citations

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    phantoms = collect_phantom_citations(
        ["real-story", "phantom-one", "phantom-two"],
        tmp_path,
        citing_kind="feature",
    )
    assert phantoms == ["phantom-one", "phantom-two"]


def test_collect_phantom_citations_ticket_resolves_against_features_or_stories(
    tmp_path: Path,
) -> None:
    """Ticket sources can cite features or stories. Phantom detection
    has to check both registries."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.workflow import collect_phantom_citations

    StoryRegistry(tmp_path).write(StoryPayload(
        title="A real story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="A real feature",
        description="d", tickets=[],
        stack_span="full-stack", tier="v1",
        sources=["a-real-story"],
    ))
    # All three should resolve when citing-kind is ticket.
    phantoms = collect_phantom_citations(
        ["a-real-story", "a-real-feature", "phantom-thing"],
        tmp_path,
        citing_kind="ticket",
    )
    assert phantoms == ["phantom-thing"]


def test_collect_phantom_citations_resolves_guid_form(
    tmp_path: Path,
) -> None:
    """``<guid>:<slug>`` form is the P18 canonical citation. Each
    half can resolve independently."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.workflow import collect_phantom_citations

    story = StoryRegistry(tmp_path).write(StoryPayload(
        title="A specific story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    # GUID form alone resolves.
    assert collect_phantom_citations(
        [story.guid], tmp_path, citing_kind="feature",
    ) == []
    # guid:slug form resolves.
    assert collect_phantom_citations(
        [f"{story.guid}:a-specific-story"],
        tmp_path, citing_kind="feature",
    ) == []
    # Phantom guid surfaces as phantom.
    bogus_guid = "01XXXXXXXXXXXXXXXXXXXXXXXX"
    assert collect_phantom_citations(
        [bogus_guid], tmp_path, citing_kind="feature",
    ) == [bogus_guid]


def test_load_features_drops_when_all_sources_phantom(
    tmp_path: Path,
) -> None:
    """A feature whose EVERY source is a phantom is fully unmoored —
    drop from seed pool. Operator-visible WARNING surfaces the
    cleanup."""
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.seeds_fallback import _load_features

    # No stories registered → both citations are phantoms.
    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Fully unmoored",
        description="d", tickets=[],
        stack_span="full-stack", tier="v1",
        sources=["ghost-story-one", "ghost-story-two"],
    ))

    loaded = _load_features(tmp_path)
    assert all(r.slug != "fully-unmoored" for r in loaded), (
        "feature with NO resolving sources should be dropped"
    )


def test_load_features_keeps_record_with_partial_phantom_citations(
    tmp_path: Path,
) -> None:
    """At-least-one-anchor semantics: a feature whose sources are
    a mix of real + phantom is well-anchored via the real one;
    keep it. The earlier all-must-resolve rule was too strict and
    silently filtered tickets whose Sources legitimately cited
    process artifacts (review slugs, build-check refs) alongside
    the parent feature — observed on obol-demo2 M1 where the
    pipeline iterated only the 3 done tickets while 5+ legitimate
    queued tickets were filtered out."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.seeds_fallback import _load_features

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Anchored",
        description="d", tickets=[],
        stack_span="full-stack", tier="v1",
        # One real, one phantom — anchored.
        sources=["real-story", "phantom-extra-reference"],
    ))

    loaded = _load_features(tmp_path)
    slugs = {r.slug for r in loaded}
    assert "anchored" in slugs, (
        "feature with at least one resolving source must be kept"
    )


def test_load_features_keeps_clean_features_when_active_milestone_scope_is_none(
    tmp_path: Path,
) -> None:
    """No active milestone scope → milestone-scope filter doesn't
    apply, but the phantom-citation filter still does."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.seeds_fallback import _load_features

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Clean feature",
        description="d", tickets=[],
        stack_span="full-stack", tier="v1",
        sources=["real-story"],
    ))

    loaded = _load_features(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].slug == "clean-feature"


def test_load_tickets_drops_when_all_sources_phantom(
    tmp_path: Path,
) -> None:
    """Same at-least-one-anchor semantic for tickets. Substrate-
    synthesized follow-up tickets legitimately cite review slugs
    (``build-check-verify-failed``, etc.) alongside the parent
    feature — those review citations look phantom to the
    feature/story-only resolver but are real process references.
    Drop the ticket only when NO source resolves at all."""
    from wonderland.story import StoryPayload, StoryRegistry
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.seeds_fallback import _load_tickets

    StoryRegistry(tmp_path).write(StoryPayload(
        title="Real story",
        persona="Kohl", situation="x", need="As Kohl I want y so z.",
        acceptance=["a"], tier="core", confusion_flags=["c"],
    ))
    FeatureRegistry(tmp_path).write(FeaturePayload(
        title="Real feature",
        description="d", tickets=[],
        stack_span="full-stack", tier="v1",
        sources=["real-story"],
    ))
    TicketRegistry(tmp_path).write(TicketPayload(
        title="Clean ticket",
        owner="tweedledum", tier="v1", estimate="1d",
        description="d", sources=["real-feature"],
    ))
    # Mixed sources: real feature + phantom — well-anchored; KEEP.
    TicketRegistry(tmp_path).write(TicketPayload(
        title="Anchored review followup",
        owner="tweedledee", tier="v1", estimate="1d",
        description="d",
        sources=["real-feature", "build-check-verify-failed"],
    ))
    # ALL phantom — fully unmoored; DROP.
    TicketRegistry(tmp_path).write(TicketPayload(
        title="Fully unmoored",
        owner="tweedledum", tier="v1", estimate="1d",
        description="d",
        sources=["ghost-feature", "another-ghost"],
    ))

    loaded = _load_tickets(tmp_path)
    slugs = {r.slug for r in loaded}
    assert "clean-ticket" in slugs
    assert "anchored-review-followup" in slugs, (
        "ticket anchored via real feature must be kept despite extra phantom citation"
    )
    assert "fully-unmoored" not in slugs, (
        "ticket whose every source is phantom must be dropped"
    )


def test_phantom_filter_keeps_feature_with_queued_work(tmp_path: Path) -> None:
    """A feature whose upstream citations are ALL phantom must NOT be
    dropped when it has queued/in-progress work — otherwise the operator's
    queued tickets silently vanish from the implement lane (the
    'No tickets to work' bug)."""
    from wonderland.coverage import _parse_feature_sources
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.seeds_fallback import _filter_phantom_citations
    from wonderland.ticket import TicketPayload, TicketRegistry
    from wonderland.ticket_lifecycle import TicketState, transition

    feat = FeatureRegistry(tmp_path).write(FeaturePayload(
        title="live time card", description="d", stack_span="full-stack",
        tier="v1", personas=["p"], tickets=[],
        sources=["ghost-story-that-does-not-exist-on-disk"], milestone=None))
    tk = TicketRegistry(tmp_path).write(TicketPayload(
        title="build the time card", owner="tweedledum", tier="v1",
        estimate="1d", description="d", sources=[feat.slug]))
    transition(tmp_path, tk.slug, TicketState.QUEUED, by="operator")

    records = FeatureRegistry(tmp_path).list_features()
    kept = _filter_phantom_citations(
        records, tmp_path, citing_kind="feature",
        sources_parser=_parse_feature_sources,
    )
    # Feature survives despite all-phantom sources, because its ticket is queued.
    assert any(r.slug == feat.slug for r in kept)


def test_phantom_filter_drops_feature_with_no_live_work(tmp_path: Path) -> None:
    """Control: an all-phantom feature with NO queued/in-progress work is
    still dropped (the exemption is scoped to live work only)."""
    from wonderland.coverage import _parse_feature_sources
    from wonderland.feature import FeaturePayload, FeatureRegistry
    from wonderland.seeds_fallback import _filter_phantom_citations

    feat = FeatureRegistry(tmp_path).write(FeaturePayload(
        title="orphan feature", description="d", stack_span="full-stack",
        tier="v1", personas=["p"], tickets=[],
        sources=["ghost-story-that-does-not-exist-on-disk"], milestone=None))
    kept = _filter_phantom_citations(
        FeatureRegistry(tmp_path).list_features(), tmp_path,
        citing_kind="feature", sources_parser=_parse_feature_sources,
    )
    assert all(r.slug != feat.slug for r in kept)
