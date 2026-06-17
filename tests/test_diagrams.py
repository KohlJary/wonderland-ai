"""Tests for the diagram registry (P21 chunk 1) — durable slug-linkage
identity over Ophanic ``.oph`` diagrams.

Diagrams follow Ophanic's box-per-component convention (each component
ref in its own box) so node extraction is complete.
"""

from __future__ import annotations

from pathlib import Path

from wonderland.diagrams import DiagramRegistry, LAYER_DB, LAYER_UI
from wonderland.diagrams._ophanic.models import NodeType
from wonderland.diagrams.links import (
    DiagramLinks,
    STATUS_BUILT,
    STATUS_IN_PROGRESS,
    STATUS_PENDING,
    STATUS_UNLINKED,
)
from wonderland.ticket_lifecycle import TicketState, back_fill_state, transition

# Realistic dashboard shape: full-width navbar over a row of
# [Sidebar | ContentArea]. Rows wrapped in their own box so the hierarchy
# captures navbar-above / sidebar-content-beside (with proportions).
_DASH_OPH = """# Dashboard

@desktop
┌──────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────┐   │
│ │ ◆Navbar                                    │   │
│ └────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────┐ │
│ │ ┌──────────────────┐ ┌─────────────────────┐ │ │
│ │ │ ◆Sidebar         │ │ ◆ContentArea        │ │ │
│ │ └──────────────────┘ └─────────────────────┘ │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
"""

_APP_OPH = """# App

@desktop
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆Navbar            │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ ◆Sidebar           │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ ◆ContentArea       │ │
│ └────────────────────┘ │
└────────────────────────┘

## ◆Sidebar
@default
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆NavLinks          │ │
│ └────────────────────┘ │
└────────────────────────┘
"""

_SCHEMA_OPH = """# Schema

@default
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆users             │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ ◆orders            │ │
│ └────────────────────┘ │
└────────────────────────┘
"""


def test_write_read_roundtrip(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("App", _APP_OPH, layer=LAYER_UI)
    assert d.slug == "app"
    assert d.layer == LAYER_UI
    assert d.title == "App"
    assert (tmp_path / ".wonderland" / "diagrams" / "app.oph").is_file()
    again = reg.read("app")
    assert again is not None
    assert again.guid == d.guid


def test_extracts_all_nodes_including_nested_def(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("App", _APP_OPH)
    names = {n.name for n in d.nodes}
    # Top-level refs + the ref nested inside the Sidebar component def.
    assert names == {"Navbar", "Sidebar", "ContentArea", "NavLinks"}
    # Sidebar is a definition (## ◆Sidebar); the rest are refs.
    assert d.node_by_name("Sidebar").is_defined is True
    assert d.node_by_name("Navbar").is_defined is False


def test_node_guids_stable_across_reread(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d1 = reg.write("App", _APP_OPH)
    d2 = reg.read("app")
    g1 = {n.name: n.guid for n in d1.nodes}
    g2 = {n.name: n.guid for n in d2.nodes}
    assert g1 == g2


def test_rename_preserves_guid(tmp_path: Path) -> None:
    """The slug-linkage property: a node's GUID survives a display-name
    rename, so any ticket linked to it stays linked."""
    reg = DiagramRegistry(tmp_path)
    d = reg.write("App", _APP_OPH)
    sidebar_guid = d.node_by_name("Sidebar").guid
    assert reg.rename_node(sidebar_guid, "LeftRail") is True
    # The GUID still resolves; only the label changed in the index.
    idx = (tmp_path / ".wonderland" / "diagrams" / "index.json").read_text()
    assert "LeftRail" in idx
    assert sidebar_guid in idx


def test_rewrite_preserves_diagram_and_node_guids(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d1 = reg.write("App", _APP_OPH)
    navbar_guid = d1.node_by_name("Navbar").guid
    # Re-publish the same diagram (e.g. design updates it).
    d2 = reg.write("App", _APP_OPH)
    assert d2.guid == d1.guid  # diagram identity preserved
    assert d2.node_by_name("Navbar").guid == navbar_guid  # node identity too


def test_layer_separation(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("App", _APP_OPH, layer=LAYER_UI)
    reg.write("Schema", _SCHEMA_OPH, layer=LAYER_DB)
    layers = {n.layer for n in reg.all_nodes()}
    assert layers == {LAYER_UI, LAYER_DB}
    db_nodes = {n.name for n in reg.nodes("schema")}
    assert db_nodes == {"users", "orders"}
    assert all(n.layer == LAYER_DB for n in reg.nodes("schema"))


def test_list_and_find(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("App", _APP_OPH)
    reg.write("Schema", _SCHEMA_OPH, layer=LAYER_DB)
    assert reg.list_slugs() == ["app", "schema"]
    a_node = reg.nodes("app")[0]
    found = reg.find_node(a_node.guid)
    assert found is not None
    assert found.guid == a_node.guid


def test_read_missing_returns_none(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    assert reg.read("nope") is None
    assert reg.nodes("nope") == []
    assert reg.list_slugs() == []


# ---------- realistic nested structure ----------


def test_captures_navbar_over_row_structure(tmp_path: Path) -> None:
    """The canonical dashboard shape: navbar above a row of
    [Sidebar | ContentArea], with the nesting + proportions intact."""
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Dashboard", _DASH_OPH)
    assert {n.name for n in d.nodes} == {"Navbar", "Sidebar", "ContentArea"}
    # Structure: outer column = [Navbar, row=[Sidebar, ContentArea]]
    root = d.document.breakpoints[0].root
    refs_top = [c.name for c in root.children if c.type == NodeType.COMPONENT_REF]
    rows = [c for c in root.children if c.type == NodeType.CONTAINER]
    assert "Navbar" in refs_top
    assert len(rows) == 1  # the sidebar/content row
    row_kids = {c.name for c in rows[0].children}
    assert row_kids == {"Sidebar", "ContentArea"}
    # Side-by-side → proportional widths recovered.
    sidebar = next(c for c in rows[0].children if c.name == "Sidebar")
    assert sidebar.width_proportion is not None
    assert 0.0 < sidebar.width_proportion.value < 1.0


# ---------- links + built/pending status ----------


def test_links_many_to_many(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Dashboard", _DASH_OPH)
    links = DiagramLinks(tmp_path)
    navbar = d.node_by_name("Navbar").guid
    sidebar = d.node_by_name("Sidebar").guid

    # One ticket realizing two nodes; one node realized by two tickets.
    links.link(navbar, "ticket-shell")
    links.link(sidebar, "ticket-shell")
    links.link(navbar, "ticket-navbar")
    links.link(navbar, "ticket-navbar")  # idempotent

    assert set(links.nodes_for_target("ticket-shell")) == {navbar, sidebar}
    assert set(links.ticket_slugs_for_node(navbar)) == {"ticket-shell", "ticket-navbar"}


def test_node_status_derived_from_tickets(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Dashboard", _DASH_OPH)
    links = DiagramLinks(tmp_path)
    navbar = d.node_by_name("Navbar").guid
    sidebar = d.node_by_name("Sidebar").guid
    content = d.node_by_name("ContentArea").guid

    # Unlinked node.
    assert links.node_status(content) == STATUS_UNLINKED

    # Navbar: two tickets, both done → built.
    for t in ("t-nav-a", "t-nav-b"):
        links.link(navbar, t)
        back_fill_state(tmp_path, t, TicketState.IN_PROGRESS)
        transition(tmp_path, t, TicketState.DONE, by="test")
    assert links.node_status(navbar) == STATUS_BUILT

    # Sidebar: one done, one in progress → in_progress.
    links.link(sidebar, "t-sb-done")
    back_fill_state(tmp_path, "t-sb-done", TicketState.IN_PROGRESS)
    transition(tmp_path, "t-sb-done", TicketState.DONE, by="test")
    links.link(sidebar, "t-sb-wip")
    back_fill_state(tmp_path, "t-sb-wip", TicketState.IN_PROGRESS)
    assert links.node_status(sidebar) == STATUS_IN_PROGRESS


def test_node_status_pending_and_aborted(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Dashboard", _DASH_OPH)
    links = DiagramLinks(tmp_path)
    navbar = d.node_by_name("Navbar").guid

    # Linked but ticket never started (no lifecycle state) → pending.
    links.link(navbar, "t-fresh")
    assert links.node_status(navbar) == STATUS_PENDING

    # An aborted-only node reads pending (aborted work doesn't count built).
    content = d.node_by_name("ContentArea").guid
    links.link(content, "t-abandoned")
    back_fill_state(tmp_path, "t-abandoned", TicketState.IN_PROGRESS)
    transition(tmp_path, "t-abandoned", TicketState.ABORTED, by="test")
    assert links.node_status(content) == STATUS_PENDING


def test_unlink(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Dashboard", _DASH_OPH)
    links = DiagramLinks(tmp_path)
    navbar = d.node_by_name("Navbar").guid
    links.link(navbar, "t1")
    assert links.unlink(navbar, "t1") is True
    assert links.links_for_node(navbar) == []
    assert links.unlink(navbar, "t1") is False  # already gone


# ---------- milestone_plan emission (P21 chunk 2) ----------


def test_rabbit_diagram_decision_records_to_registry(tmp_path: Path) -> None:
    """The diagram meeting: a Rabbit `diagram` decision writes the .oph
    through DiagramRegistry and returns a node-bearing artifact."""
    from wonderland.agents.white_rabbit import RabbitResponse, WhiteRabbit
    from wonderland.diagrams.payload import DiagramPayload

    # Schema: decision='diagram' requires diagrams.
    resp = RabbitResponse(
        decision="diagram",
        diagrams=[DiagramPayload(name="Dashboard", oph=_DASH_OPH, layer="ui")],
    )
    import pytest
    with pytest.raises(Exception):
        RabbitResponse(decision="diagram", diagrams=[])

    # Recorder writes to the registry + emits an artifact.
    rb = WhiteRabbit.__new__(WhiteRabbit)
    rb._diagram_registry = DiagramRegistry(tmp_path)
    artifacts = rb._record_diagrams(resp.diagrams)
    assert len(artifacts) == 1
    art = artifacts[0]
    assert art.kind == "diagram"
    assert art.payload["slug"] == "dashboard"
    assert {n["name"] for n in art.payload["nodes"]} == {
        "Navbar", "Sidebar", "ContentArea",
    }
    assert DiagramRegistry(tmp_path).list_slugs() == ["dashboard"]


def test_alice_diagram_decision_records_to_registry(tmp_path: Path) -> None:
    """Alice can now author diagrams too (P21 — she's on the diagram
    meeting roster). Same shared recorder as the Rabbit."""
    from wonderland.agents.alice import Alice, AliceResponse
    from wonderland.diagrams.payload import DiagramPayload
    from wonderland.diagrams.recording import record_diagrams

    resp = AliceResponse(
        decision="diagram",
        diagrams=[DiagramPayload(name="Dashboard", oph=_DASH_OPH, layer="ui")],
    )
    import pytest
    with pytest.raises(Exception):
        AliceResponse(decision="diagram", diagrams=[])

    arts = record_diagrams(DiagramRegistry(tmp_path), resp.diagrams)
    assert len(arts) == 1
    assert arts[0].kind == "diagram"
    assert {n["name"] for n in arts[0].payload["nodes"]} == {
        "Navbar", "Sidebar", "ContentArea",
    }
    assert DiagramRegistry(tmp_path).list_slugs() == ["dashboard"]


# --------------------------------------------------------------------- #
# Diagram dedup (P21) — cross-author same-surface folding
# --------------------------------------------------------------------- #

from wonderland.diagrams import (  # noqa: E402
    consolidate_diagrams,
    find_duplicate_diagrams,
)

# A second dashboard the way the OTHER author would draw it: same surface
# (shares Navbar + ContentArea), one extra unique component, slightly
# different framing. The dedup should fold this into the richer one.
_DASH2_OPH = """# Dashboard Page

@desktop
┌──────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────┐   │
│ │ ◆Navbar                                    │   │
│ └────────────────────────────────────────────┘   │
│ ┌──────────────────┐ ┌─────────────────────┐      │
│ │ ◆ContentArea     │ │ ◆RefreshSection     │      │
│ └──────────────────┘ └─────────────────────┘      │
└──────────────────────────────────────────────────┘
"""

# A genuinely different page that happens to share ONE chrome element
# (Navbar) — must NOT be folded (MIN_SHARED guard).
_SETTINGS_OPH = """# Settings

@desktop
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆Navbar            │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ ◆ProfileForm       │ │
│ └────────────────────┘ │
└────────────────────────┘
"""

# Malformed boxes (borders misaligned) but the ◆ sigils are intact — the
# structured parser drops these nodes; the raw-◆ fallback must catch them.
_MANGLED_OPH = """# Mangled

@desktop
┌───────────────────┐
│ ◆Header
│ ◆Body  ◆Footer   │
└─────────────
"""


def test_raw_diamond_fallback_extracts_nodes_from_malformed_boxes(
    tmp_path: Path,
) -> None:
    reg = DiagramRegistry(tmp_path)
    d = reg.write("Mangled", _MANGLED_OPH, layer=LAYER_UI)
    # Even though the boxes don't close cleanly, every ◆-ref is captured.
    assert {n.name for n in d.nodes} == {"Header", "Body", "Footer"}


def test_find_duplicate_folds_same_surface(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)
    reg.write("Dashboard Page", _DASH2_OPH, layer=LAYER_UI)
    dups = find_duplicate_diagrams(reg)
    assert len(dups) == 1
    dup = dups[0]
    # Survivor is the richer diagram (more nodes): the original _DASH_OPH
    # has Navbar/Sidebar/ContentArea (3); _DASH2 has Navbar/ContentArea/
    # RefreshSection (3) — tie broken alphabetically -> "dashboard".
    assert {dup.survivor, dup.removed} == {"dashboard", "dashboard-page"}
    assert "navbar" in dup.shared and "contentarea" in dup.shared


def test_single_shared_chrome_not_folded(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)
    reg.write("Settings", _SETTINGS_OPH, layer=LAYER_UI)
    # Share only Navbar -> below MIN_SHARED, never folded.
    assert find_duplicate_diagrams(reg) == []


def test_cross_layer_never_folded(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)
    # Same node names but a DB-layer diagram: layer guard keeps them apart.
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_DB, slug="dashboard-db")
    assert find_duplicate_diagrams(reg) == []


def test_consolidate_removes_loser_and_migrates_links(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)
    page = reg.write("Dashboard Page", _DASH2_OPH, layer=LAYER_UI)
    links = DiagramLinks(tmp_path)

    dups = find_duplicate_diagrams(reg)
    removed_slug = dups[0].removed
    survivor_slug = dups[0].survivor
    removed = reg.read(removed_slug)
    # Link a ticket to the removed diagram's Navbar node (shared surface).
    removed_navbar = removed.node_by_name("Navbar")
    links.link(removed_navbar.guid, "t-navbar")

    applied = consolidate_diagrams(tmp_path, registry=reg, links=links)
    assert len(applied) == 1
    # Loser diagram gone; survivor remains.
    assert removed_slug not in reg.list_slugs()
    assert survivor_slug in reg.list_slugs()
    # The link migrated onto the survivor's same-named Navbar node.
    survivor = reg.read(survivor_slug)
    survivor_navbar = survivor.node_by_name("Navbar")
    assert ("ticket", "t-navbar") in links.links_for_node(survivor_navbar.guid)
    assert links.links_for_node(removed_navbar.guid) == []


def test_consolidate_noop_when_no_duplicates(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)
    reg.write("Settings", _SETTINGS_OPH, layer=LAYER_UI)
    assert consolidate_diagrams(tmp_path, registry=reg) == []
    assert set(reg.list_slugs()) == {"dashboard", "settings"}


# --------------------------------------------------------------------- #
# Diagram-node ↔ ticket auto-linking (P21 chunk b)
# --------------------------------------------------------------------- #

from wonderland.diagrams.linking import (  # noqa: E402
    _distinctive_tokens,
    _name_matches,
    _title_tokens,
    link_tickets_to_nodes,
)
from wonderland.ticket import TicketPayload, TicketRegistry  # noqa: E402

_SIGNIN_OPH = """# Sign In

@desktop
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆SignInForm        │ │
│ └────────────────────┘ │
└────────────────────────┘
"""

_USERS_SCHEMA_OPH = """# Users Schema

@default
┌────────────────────────┐
│ ┌────────────────────┐ │
│ │ ◆UsersTable        │ │
│ └────────────────────┘ │
└────────────────────────┘
"""


def _ticket(tmp_path, title, *, stack_span="full-stack", slug_src="feat-x"):
    return TicketRegistry(tmp_path).write(TicketPayload(
        title=title, owner="tweedledum", tier="v1",
        estimate="1d", description="d", sources=[slug_src],
        stack_span=stack_span,
    ))


def test_distinctive_tokens_drops_generic_suffix() -> None:
    assert _distinctive_tokens("DashboardPage") == {"dashboard"}
    assert _distinctive_tokens("SignInForm") == {"sign", "in"}
    # "table" is KEPT distinctive (DB discriminator).
    assert _distinctive_tokens("UsersTable") == {"users", "table"}
    # all-generic name -> empty (chrome, never matches).
    assert _distinctive_tokens("ContentArea") == frozenset()


def test_name_matches_requires_all_distinctive_tokens() -> None:
    assert _name_matches({"sign", "in"}, _title_tokens("Build the sign in form"))
    assert not _name_matches({"sign", "in"}, _title_tokens("Build the sign up form"))
    # 4-char real nouns ARE trusted (Time/News card nodes must link).
    assert _name_matches({"news"}, _title_tokens("Add a news widget"))
    assert _name_matches({"time"}, _title_tokens("Time card client-side render"))
    # 3-and-under lone tokens are not (throwaway: api/ui/db).
    assert not _name_matches({"api"}, _title_tokens("Build the api layer"))
    # lone long token is.
    assert _name_matches({"dashboard"}, _title_tokens("Render the dashboard"))


def test_links_node_to_matching_ticket(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    _ticket(tmp_path, "Implement the sign-in form", stack_span="frontend")

    result = link_tickets_to_nodes(tmp_path)
    assert len(result.created) == 1
    link = result.created[0]
    assert link.node_name == "SignInForm"
    # node_status now reflects a linked-but-unstarted ticket.
    node = reg.read("sign-in").node_by_name("SignInForm")
    assert DiagramLinks(tmp_path).node_status(node.guid) == STATUS_PENDING


def test_layer_gate_blocks_cross_layer(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    # A backend-only ticket whose title would match by name — layer gate
    # must keep a ui node off it.
    _ticket(tmp_path, "Sign in form session backend", stack_span="backend")
    assert link_tickets_to_nodes(tmp_path).created == []


def test_table_discriminator(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Users Schema", _USERS_SCHEMA_OPH, layer=LAYER_DB)
    _ticket(tmp_path, "Create users table migration", stack_span="backend")
    _ticket(tmp_path, "Build the users API list endpoint", stack_span="backend",
            slug_src="feat-y")
    created = link_tickets_to_nodes(tmp_path).created
    # UsersTable links the migration, NOT the API endpoint.
    assert len(created) == 1
    assert created[0].ticket_title == "Create users table migration"


def test_chrome_node_stays_unlinked(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_OPH, layer=LAYER_UI)  # has ◆ContentArea
    _ticket(tmp_path, "Build the content area wrapper", stack_span="frontend")
    result = link_tickets_to_nodes(tmp_path)
    # ContentArea is all-generic -> never linked.
    assert all(l.node_name != "ContentArea" for l in result.created)
    assert "dashboard:ContentArea" in result.unlinked_nodes


def test_linking_idempotent(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    _ticket(tmp_path, "Implement the sign-in form", stack_span="frontend")
    first = link_tickets_to_nodes(tmp_path)
    second = link_tickets_to_nodes(tmp_path)
    assert len(first.created) == len(second.created) == 1
    node = reg.read("sign-in").node_by_name("SignInForm")
    # No duplicate link rows.
    assert len(DiagramLinks(tmp_path).links_for_node(node.guid)) == 1


def test_db_node_matches_schema_migration_vocabulary(tmp_path: Path) -> None:
    # Real ldr-ophanic gap: a UsersTable node must link a ticket that says
    # "schema & migrations" (not the literal word "table"), but still NOT
    # an unrelated "users API" ticket.
    reg = DiagramRegistry(tmp_path)
    reg.write("Users Schema", _USERS_SCHEMA_OPH, layer=LAYER_DB)
    _ticket(tmp_path, "SQLite schema and migrations for users and partners",
            stack_span="backend")
    _ticket(tmp_path, "Build the users API list endpoint", stack_span="backend",
            slug_src="feat-y")
    created = link_tickets_to_nodes(tmp_path).created
    assert len(created) == 1
    assert "schema and migrations" in created[0].ticket_title


def test_db_synonym_does_not_leak_to_ui_nodes() -> None:
    from wonderland.diagrams.linking import _name_matches
    from wonderland.diagrams import LAYER_DB, LAYER_UI
    # A ui node with a literal "table" token is NOT expanded to schema/etc.
    assert _name_matches({"pricing", "table"},
                         _title_tokens("pricing table component"), LAYER_UI)
    assert not _name_matches({"pricing", "table"},
                             _title_tokens("pricing schema migration"), LAYER_UI)
    # The db node IS expanded.
    assert _name_matches({"users", "table"},
                         _title_tokens("users schema migration"), LAYER_DB)


def test_nav_reference_target_does_not_link(tmp_path: Path) -> None:
    # A sign-out ticket that says "redirect to sign-in" must NOT link the
    # SignIn node (it references sign-in as a destination, doesn't build it).
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    _ticket(tmp_path, "Sign-out button on dashboard + redirect to sign-in",
            stack_span="frontend")
    assert link_tickets_to_nodes(tmp_path).created == []


def test_conjunction_surface_still_links(tmp_path: Path) -> None:
    # "Sign-up AND sign-in flows" builds both — the nav-ref strip must not
    # eat a surface joined by "and".
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    _ticket(tmp_path, "Sign-up and sign-in flows with session handling",
            stack_span="frontend")
    created = link_tickets_to_nodes(tmp_path).created
    assert any(c.node_name == "SignInForm" for c in created)


def _feature(tmp_path, slug):
    from wonderland.feature import FeaturePayload, FeatureRegistry, StackSpan
    from wonderland.ticket import TicketTier
    return FeatureRegistry(tmp_path).write(FeaturePayload(
        title=slug.replace("-", " "), description="parent feature",
        stack_span=StackSpan.FULL_STACK, personas=["p"], tickets=[],
        tier=TicketTier.V1, sources=["some-story"], milestone=None,
    ))


def test_orphan_ticket_not_linked(tmp_path: Path) -> None:
    # A ticket that cites no on-disk feature (orphan — points only at a
    # milestone) is culled work; it must not light up a node, even when its
    # title would match by name. ldr-ophanic M2: the leaked weather/news
    # tickets were orphans and were falsely showing nodes as pending.
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", _SIGNIN_OPH, layer=LAYER_UI)
    _feature(tmp_path, "auth-feature")
    _ticket(tmp_path, "Implement the sign-in form", stack_span="frontend",
            slug_src="auth-feature")          # feature-attached -> links
    _ticket(tmp_path, "Sign-in form leaked orphan", stack_span="frontend",
            slug_src="m9-some-milestone")     # orphan -> filtered
    created = link_tickets_to_nodes(tmp_path).created
    assert any("Implement" in c.ticket_title for c in created)
    assert all("orphan" not in c.ticket_title for c in created)


def test_diagram_in_milestone_scope_matches_named_nodes() -> None:
    # P21 seed scoping: a diagram is in-scope for a milestone iff one of its
    # nodes is named in the milestone text.
    from wonderland.seeds_fallback import _diagram_in_milestone_scope
    from wonderland.diagrams.linking import _title_tokens

    class _D:
        def __init__(self, names):
            self.nodes = [type("N", (), {"name": n}) for n in names]

    weather_text = _title_tokens(
        "Weather card renders cached conditions with stale indicator"
    )
    assert _diagram_in_milestone_scope(_D(["WeatherCard", "CardGrid"]), weather_text)
    # auth diagram has no node named in the weather milestone → out of scope
    assert not _diagram_in_milestone_scope(
        _D(["SignInForm", "SignInPage"]), weather_text
    )


def test_tdd_implement_seeds_diagrams_to_tweedles() -> None:
    # P21 (c): the M7 implementation meeting must seed the structural
    # diagrams so the Tweedles build + wire components against the contract.
    from wonderland.workflow import load_workflow

    wf = load_workflow("tdd-implement")
    m7 = next(m for m in wf.meetings if m.id == "implementation")
    seed_kinds = {k for s in m7.seeds for k in s.kinds}
    assert "diagram" in seed_kinds


# --------------------------------------------------------------------- #
# Wiring-diff (P21 d) — reverse-adapt built code vs intended diagram
# --------------------------------------------------------------------- #

from wonderland.diagrams.wiring import (  # noqa: E402
    STATUS_MISSING,
    STATUS_ORPHANED,
    STATUS_WIRED,
    verify_wiring,
)

# Clean box-per-component dashboard: Navbar over a row of three cards.
_DASH_CARDS_OPH = """# Dashboard

@desktop
┌──────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────┐   │
│ │ ◆Navbar                                    │   │
│ └────────────────────────────────────────────┘   │
│ ┌──────────┐ ┌──────────────┐ ┌──────────────┐   │
│ │ ◆TimeCard│ │ ◆WeatherCard │ │ ◆NewsCard    │   │
│ └──────────┘ └──────────────┘ └──────────────┘   │
└──────────────────────────────────────────────────┘
"""


def _write_src(tmp_path: Path, name: str, body: str) -> None:
    src = tmp_path / "src"
    src.mkdir(exist_ok=True)
    (src / name).write_text(body, encoding="utf-8")


def test_wiring_flags_orphaned_component(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_CARDS_OPH, layer=LAYER_UI, slug="dashboard")
    # Dashboard renders Navbar/TimeCard/WeatherCard but NOT NewsCard.
    _write_src(tmp_path, "Dashboard.tsx",
               "import Navbar from './Navbar';\n"
               "import TimeCard from './TimeCard';\n"
               "import WeatherCard from './WeatherCard';\n"
               "export default function Dashboard(){return(<div>"
               "<Navbar/><TimeCard/><WeatherCard/></div>);}")
    for c in ("Navbar", "TimeCard", "WeatherCard", "NewsCard"):
        _write_src(tmp_path, f"{c}.tsx",
                   f"export default function {c}(){{return <div/>;}}")
    by = {f.node: f.status for f in verify_wiring(tmp_path)}
    assert by["WeatherCard"] == STATUS_WIRED
    assert by["TimeCard"] == STATUS_WIRED
    assert by["Navbar"] == STATUS_WIRED
    # NewsCard.tsx exists but nothing renders/imports it → hollow.
    assert by["NewsCard"] == STATUS_ORPHANED


def test_wiring_flags_missing_component(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_CARDS_OPH, layer=LAYER_UI, slug="dashboard")
    # Only Dashboard + WeatherCard exist; the rest are unbuilt.
    _write_src(tmp_path, "Dashboard.tsx",
               "import WeatherCard from './WeatherCard';\n"
               "export default function Dashboard(){return <WeatherCard/>;}")
    _write_src(tmp_path, "WeatherCard.tsx",
               "export default function WeatherCard(){return <div/>;}")
    by = {f.node: f.status for f in verify_wiring(tmp_path)}
    assert by["WeatherCard"] == STATUS_WIRED
    assert by["TimeCard"] == STATUS_MISSING
    assert by["NewsCard"] == STATUS_MISSING


def test_wiring_db_layer_presence(tmp_path: Path) -> None:
    reg = DiagramRegistry(tmp_path)
    reg.write("Schema", _SCHEMA_OPH, layer=LAYER_DB, slug="schema")  # users, orders
    (tmp_path / "src").mkdir(exist_ok=True)
    (tmp_path / "src" / "models.py").write_text(
        "class Users:\n    email: str\n", encoding="utf-8")
    by = {f.node: f.status for f in verify_wiring(tmp_path)}
    assert by["users"] == "present"
    assert by["orders"] == STATUS_MISSING


def test_tdd_implement_review_seeds_diagrams_and_tool() -> None:
    # P21 (d): M8 review seeds the diagrams + verify_wiring is a tool.
    from wonderland.workflow import load_workflow

    wf = load_workflow("tdd-implement")
    m8 = next(m for m in wf.meetings if m.id == "review")
    assert "diagram" in {k for s in m8.seeds for k in s.kinds}

    from wonderland.tools import Tools
    schema_names = {t["name"] for t in Tools.tool_schemas()} if hasattr(
        Tools, "tool_schemas"
    ) else set()
    assert hasattr(Tools, "verify_wiring")


def test_wiring_milestone_scoped(tmp_path: Path) -> None:
    # P21 (d) refinement: verify_wiring only checks the ACTIVE milestone's
    # diagrams, so an M1 review doesn't flag M2-M4 surfaces as missing.
    import wonderland.workflow as wf
    reg = DiagramRegistry(tmp_path)
    reg.write("Sign In", "# Sign In\n@d\n┌────────┐\n│ ◆SignIn│\n└────────┘\n",
              layer=LAYER_UI, slug="sign-in")
    reg.write("Dashboard",
              "# Dashboard\n@d\n┌──────────────┐\n│ ◆WeatherCard │\n└──────────────┘\n",
              layer=LAYER_UI, slug="dashboard")
    ms = tmp_path / ".wonderland" / "milestones"
    ms.mkdir(parents=True, exist_ok=True)
    (ms / "milestone-01AAAAAA-m1-auth.md").write_text(
        "## Milestone 01\n**Slug:** m1-auth\n**Goal:**\nKohl can sign in\n")
    (tmp_path / "src").mkdir(exist_ok=True)
    scope = type("S", (), {"slug": "m1-auth"})()
    tok = wf.set_active_milestone_scope(scope)
    try:
        nodes = {f.node for f in verify_wiring(tmp_path)}
    finally:
        wf.set_active_milestone_scope(None)
    assert "SignIn" in nodes
    assert "WeatherCard" not in nodes  # M2 surface excluded from M1 review


def test_find_hollow_builds_cross_references_b_and_d(tmp_path: Path) -> None:
    # (b)+(d): a node a DONE ticket claims but that isn't in the code is a
    # hollow build; a node that's built+wired is not; a node with no done
    # ticket is ignored (filters verify_wiring's standalone noise).
    from wonderland.diagrams.links import DiagramLinks
    from wonderland.diagrams.wiring import find_hollow_builds
    from wonderland.ticket_lifecycle import TicketState, transition

    reg = DiagramRegistry(tmp_path)
    reg.write("Dashboard", _DASH_CARDS_OPH, layer=LAYER_UI, slug="dashboard")
    # WeatherCard built + wired; TimeCard never built.
    _write_src(tmp_path, "Dashboard.tsx",
               "import WeatherCard from './WeatherCard';\n"
               "export default function Dashboard(){return <WeatherCard/>;}")
    _write_src(tmp_path, "WeatherCard.tsx",
               "export default function WeatherCard(){return <div/>;}")
    _feature(tmp_path, "dash-feat")
    links = DiagramLinks(tmp_path)
    tc = _ticket(tmp_path, "Frontend time card component", stack_span="frontend",
                 slug_src="dash-feat")
    wc = _ticket(tmp_path, "Frontend weather card component", stack_span="frontend",
                 slug_src="dash-feat-2")
    links.link(reg.read("dashboard").node_by_name("TimeCard").guid, tc.slug)
    links.link(reg.read("dashboard").node_by_name("WeatherCard").guid, wc.slug)
    for t in (tc, wc):
        transition(tmp_path, t.slug, TicketState.QUEUED, by="op")
        transition(tmp_path, t.slug, TicketState.IN_PROGRESS, by="op")
        transition(tmp_path, t.slug, TicketState.DONE, by="op")
    hollow = {h.node for h in find_hollow_builds(tmp_path)}
    assert "TimeCard" in hollow          # done ticket + not in code → hollow
    assert "WeatherCard" not in hollow   # done ticket + built+wired → ok
    assert "Navbar" not in hollow        # no done ticket → not flagged (noise filtered)
