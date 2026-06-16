"""Node ↔ ticket/feature links + built-vs-pending view (P21 chunk 1).

Many-to-many links between diagram nodes (by durable GUID) and
tickets/features (by slug). Stored in ``.wonderland/diagrams/links.json``.
A node's *status* is a VIEW derived from its linked tickets' lifecycle —
never stored, so the diagram can never disagree with the ticket ledger
(the single source of truth). This is what turns the diagram into a live
map of what's actually built vs pending.
"""

from __future__ import annotations

import json
from pathlib import Path

from wonderland.ticket_lifecycle import TicketState, get_state

LINK_TICKET = "ticket"
LINK_FEATURE = "feature"

# Node build statuses (derived).
STATUS_UNLINKED = "unlinked"   # no ticket realizes this node yet
STATUS_PENDING = "pending"     # linked, but no work started/finished
STATUS_IN_PROGRESS = "in_progress"  # some linked work underway/done
STATUS_BUILT = "built"         # every (non-aborted) linked ticket is done


class DiagramLinks:
    """Read/write the node↔target link store + derive node build status."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root
        self._path = (
            project_root / ".wonderland" / "diagrams" / "links.json"
        )

    # ------------------------------------------------------------------ #
    # Storage
    # ------------------------------------------------------------------ #

    def _load(self) -> list[dict]:
        if not self._path.is_file():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []

    def _save(self, links: list[dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(links, indent=2) + "\n", encoding="utf-8"
        )

    # ------------------------------------------------------------------ #
    # Link operations (many-to-many)
    # ------------------------------------------------------------------ #

    def link(
        self, node_guid: str, target_slug: str, kind: str = LINK_TICKET,
    ) -> None:
        """Link a node to a ticket/feature. Idempotent."""
        links = self._load()
        if any(
            l["node_guid"] == node_guid
            and l["target_slug"] == target_slug
            and l["kind"] == kind
            for l in links
        ):
            return
        links.append(
            {"node_guid": node_guid, "target_slug": target_slug, "kind": kind}
        )
        self._save(links)

    def unlink(
        self, node_guid: str, target_slug: str, kind: str | None = None,
    ) -> bool:
        """Remove a link. ``kind=None`` removes any kind. Returns True if
        anything was removed."""
        links = self._load()
        kept = [
            l for l in links
            if not (
                l["node_guid"] == node_guid
                and l["target_slug"] == target_slug
                and (kind is None or l["kind"] == kind)
            )
        ]
        if len(kept) != len(links):
            self._save(kept)
            return True
        return False

    def links_for_node(self, node_guid: str) -> list[tuple[str, str]]:
        """``[(kind, target_slug), ...]`` for a node."""
        return [
            (l["kind"], l["target_slug"])
            for l in self._load()
            if l["node_guid"] == node_guid
        ]

    def nodes_for_target(self, target_slug: str) -> list[str]:
        """Node GUIDs linked to a given ticket/feature slug."""
        return [
            l["node_guid"]
            for l in self._load()
            if l["target_slug"] == target_slug
        ]

    def ticket_slugs_for_node(self, node_guid: str) -> list[str]:
        return [
            slug for kind, slug in self.links_for_node(node_guid)
            if kind == LINK_TICKET
        ]

    # ------------------------------------------------------------------ #
    # Derived status — a VIEW over the ticket ledger
    # ------------------------------------------------------------------ #

    def node_status(self, node_guid: str) -> str:
        """Derive build status from the node's linked tickets' lifecycle.

        - ``unlinked``     — no ticket links
        - ``pending``      — linked, but nothing in progress or done
                             (also: every linked ticket aborted)
        - ``in_progress``  — at least one linked ticket in progress or done
        - ``built``        — every non-aborted linked ticket is DONE
        """
        ticket_slugs = self.ticket_slugs_for_node(node_guid)
        if not ticket_slugs:
            return STATUS_UNLINKED
        states = [get_state(self._project_root, s) for s in ticket_slugs]
        active = [s for s in states if s != TicketState.ABORTED]
        if not active:
            return STATUS_PENDING
        if all(s == TicketState.DONE for s in active):
            return STATUS_BUILT
        if any(s in (TicketState.IN_PROGRESS, TicketState.DONE) for s in active):
            return STATUS_IN_PROGRESS
        return STATUS_PENDING

    def status_map(self, node_guids: list[str]) -> dict[str, str]:
        return {g: self.node_status(g) for g in node_guids}


__all__ = [
    "DiagramLinks",
    "LINK_TICKET",
    "LINK_FEATURE",
    "STATUS_UNLINKED",
    "STATUS_PENDING",
    "STATUS_IN_PROGRESS",
    "STATUS_BUILT",
]
