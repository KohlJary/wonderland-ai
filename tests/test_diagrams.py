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
