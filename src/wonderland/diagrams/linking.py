"""Auto-link diagram nodes to the tickets that build them (P21 chunk b).

This is the wire that makes the build-tracker *live*: once a ticket that
realizes the ``SignInForm`` node exists, the node flips from ``unlinked``
to ``pending`` and then climbs the lifecycle ladder
(``in_progress`` → ``built``) as the Tweedles build it. Without it the
Diagrams pane is a static drawing; with it, it's a progress map.

Matching is deliberately conservative — the substrate's repeated lesson
is that loose lexical overlap false-merges (the surface-signature saga).
A node links to a ticket only when **every distinctive token** of the
node's component name appears in the ticket's title AND the layers
correspond (a ``ui`` node never links to a backend-only ticket). Generic
role suffixes (``Page``, ``Form``, ``View``…) are dropped before the
test so ``DashboardPage`` matches a ticket that just says "dashboard",
but ``table``/``schema`` are KEPT distinctive so a ``UsersTable`` node
matches the migration ticket, not a "users API" ticket. A missed link
leaves a node ``unlinked`` (visibly honest); a wrong link silently
mis-reports build progress — so we bias hard toward misses.

``sources`` can't carry node links (its validator rejects any non-feature
prefix), so this is a separate, derived index — never a second source of
truth. It's recomputed from scratch each run and is idempotent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from wonderland.diagrams.links import LINK_TICKET, DiagramLinks
from wonderland.diagrams.models import LAYER_DB, LAYER_UI
from wonderland.diagrams.registry import DiagramRegistry
from wonderland.ticket import (
    TicketRegistry,
    TicketStackSpan,
    read_ticket_stack_span,
)

# Role/shape suffixes that carry no surface identity. Dropped from a node
# name before matching. NOTE: ``table``/``schema`` are intentionally NOT
# here — for a DB node they're the discriminator between the schema ticket
# and an API ticket touching the same entity.
_GENERIC_TOKENS = frozenset(
    {
        "page", "form", "view", "screen", "panel", "section", "container",
        "area", "list", "card", "grid", "row", "column", "header", "footer",
        "modal", "dialog", "wrapper", "layout", "component", "widget",
        "field", "button", "bar", "menu", "nav", "content", "main",
    }
)

# Minimum length for a *lone* distinctive token to be trusted on its own —
# guards against a single common word (e.g. a bare "Users" node) linking
# every ticket that happens to mention it. Multi-token nodes bypass this.
_MIN_SOLO_TOKEN_LEN = 5

_CAMEL_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")
_WORD_RE = re.compile(r"[a-z0-9]+")

_UI_SPANS = frozenset({TicketStackSpan.FRONTEND, TicketStackSpan.FULL_STACK})
_DB_SPANS = frozenset({TicketStackSpan.BACKEND, TicketStackSpan.FULL_STACK})


def _split_name(name: str) -> list[str]:
    """``SignInForm`` → ``[sign, in, form]``; ``users_table`` →
    ``[users, table]``. Handles CamelCase, snake_case, digits."""
    parts: list[str] = []
    for chunk in re.split(r"[_\-\s]+", name):
        parts.extend(_CAMEL_RE.findall(chunk))
    return [p.lower() for p in parts if p]


def _distinctive_tokens(name: str) -> frozenset[str]:
    return frozenset(
        t for t in _split_name(name)
        if t not in _GENERIC_TOKENS and len(t) > 1
    )


def _title_tokens(title: str) -> frozenset[str]:
    # No stopword removal: ``in``/``up``/``on`` are real signal in
    # component names (signIN, signUP), and the subset test only ever
    # reads the node's tokens, so title noise is harmless.
    return frozenset(t for t in _WORD_RE.findall(title.lower()) if len(t) >= 2)


def _layer_allows(layer: str, span: TicketStackSpan) -> bool:
    if layer == LAYER_UI:
        return span in _UI_SPANS
    if layer == LAYER_DB:
        return span in _DB_SPANS
    return True  # unknown layer: don't gate


def _name_matches(distinctive: frozenset[str], title_toks: frozenset[str]) -> bool:
    if not distinctive or not distinctive <= title_toks:
        return False
    if len(distinctive) == 1:
        return len(next(iter(distinctive))) >= _MIN_SOLO_TOKEN_LEN
    return True


@dataclass(frozen=True)
class NodeLink:
    node_guid: str
    node_name: str
    diagram_slug: str
    layer: str
    ticket_slug: str
    ticket_title: str


@dataclass
class LinkingResult:
    created: list[NodeLink] = field(default_factory=list)
    # nodes that ended up with no linked ticket (build-progress gaps)
    unlinked_nodes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"linked={len(self.created)} unlinked_nodes={len(self.unlinked_nodes)}"
        )


def link_tickets_to_nodes(
    project_root: Path,
    *,
    registry: DiagramRegistry | None = None,
    links: DiagramLinks | None = None,
    ticket_registry: TicketRegistry | None = None,
) -> LinkingResult:
    """Match every diagram node against every ticket and write the links.
    Idempotent (``DiagramLinks.link`` dedupes). Pure derivation from the
    ticket + diagram registries — safe to re-run any time."""
    registry = registry or DiagramRegistry(project_root)
    links = links or DiagramLinks(project_root)
    ticket_registry = ticket_registry or TicketRegistry(project_root)

    tickets = ticket_registry.list_tickets()
    # Precompute (slug, title, token-set, stack-span) once.
    ticket_rows: list[tuple[str, str, frozenset[str], TicketStackSpan]] = []
    for t in tickets:
        span = read_ticket_stack_span(project_root, t.slug)
        ticket_rows.append((t.slug, t.title, _title_tokens(t.title), span))

    result = LinkingResult()
    for slug in registry.list_slugs():
        diagram = registry.read(slug)
        if diagram is None:
            continue
        for node in diagram.nodes:
            distinctive = _distinctive_tokens(node.name)
            matched_any = False
            for tslug, ttitle, ttoks, span in ticket_rows:
                if not _layer_allows(node.layer, span):
                    continue
                if _name_matches(distinctive, ttoks):
                    links.link(node.guid, tslug, LINK_TICKET)
                    result.created.append(
                        NodeLink(
                            node_guid=node.guid,
                            node_name=node.name,
                            diagram_slug=slug,
                            layer=node.layer,
                            ticket_slug=tslug,
                            ticket_title=ttitle,
                        )
                    )
                    matched_any = True
            if not matched_any and not links.links_for_node(node.guid):
                result.unlinked_nodes.append(f"{slug}:{node.name}")
    return result


__all__ = [
    "link_tickets_to_nodes",
    "LinkingResult",
    "NodeLink",
]
